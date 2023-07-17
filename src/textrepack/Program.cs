using AssetsTools.NET;
using AssetsTools.NET.Extra;
using Newtonsoft.Json;

internal class Program
{
    private static int Main(string[] args)
    {
        if (args.Length < 2)
        {
            String app = System.AppDomain.CurrentDomain.FriendlyName;
            Console.WriteLine($"usage: {app} <bundle> <json-directory>");
            return 1;
        }

        var jsons = ReadJsons(args[1]);
        PatchBundle(args[0], jsons);
        return 0;
    }

    private static Dictionary<String, TranslationScene> ReadJsons(String directory)
    {
        Console.WriteLine($"INFO: reading JSON files from {directory}");
        var result = new Dictionary<String, TranslationScene>();
        var d = new DirectoryInfo(directory);
        foreach (var file in d.GetFiles("*.json"))
        {
            var key = Path.GetFileNameWithoutExtension(file.FullName);
            using (var fi = File.OpenText(file.FullName))
            {
                var x = JsonConvert.DeserializeObject<TranslationScene>(fi.ReadToEnd());
                if (x == null)
                {
                    Console.WriteLine($"FATAL: could not read data from {file.FullName}");
                    throw new ApplicationException("Could not deserialize JSON");
                }
                result[key] = x;
            }
        }
        if (result.Count == 0)
        {
            Console.WriteLine($"FATAL: no JSON files in {directory}");
            throw new ApplicationException("No JSON files found");
        }
        Console.WriteLine($"INFO: done; read {result.Count} files");
        return result;
    }

    private static void PatchBundle(
        string filePath,
        Dictionary<String, TranslationScene> translationMap
    )
    {
        Console.WriteLine($"INFO: patching bundle file {filePath}");
        var manager = new AssetsManager();

        var bundleInstance = manager.LoadBundleFile(filePath, true);
        var assetsInstance = manager.LoadAssetsFileFromBundle(bundleInstance, 0, false);
        var assets = assetsInstance.file;

        var assetsReplacers = new List<AssetsReplacer>();

        foreach (var mono in assets.GetAssetsOfType(AssetClassID.MonoBehaviour))
        {
            var monoBase = manager.GetBaseField(assetsInstance, mono);
            var objName = monoBase["m_Name"].AsString;

            // not for any _Text there is _Text_en counterpart
            if (!objName.EndsWith("_Text") && !objName.EndsWith("_Text_en"))
                continue;

            // some _Text may contain texts in other languages than english
            var lang = monoBase["_ietfTag"].AsString;
            if (lang != "en")
                continue;

            Console.WriteLine($"DEBUG: rewrite text {objName}");
            // var sceneEntries = monoBase["_database"]["_entries"].Children;
            var sceneEntries = monoBase["_database"]["_entries"]["Array"];
            var scene = monoBase["_code"].AsString;
            var translated = translationMap.GetValueOrDefault(scene);
            if (translated == null)
            {
                if (sceneEntries.Count() > 0)
                {
                    Console.WriteLine($"ERROR: no translation file for scene {scene}");
                }
                continue;
            }
            foreach (var e in sceneEntries)
            {
                var translation = FindBestTranslation(e["_entryName"].AsString, translated);
                e["_localization"].AsString = translation;
            }

            assetsReplacers.Add(new AssetsReplacerFromMemory(assets, mono, monoBase));
        }

        var bundleReplacers = new List<BundleReplacer>();
        bundleReplacers.Add(new BundleReplacerFromAssets(assetsInstance.name, null, assets, assetsReplacers));

        using (AssetsFileWriter writer = new AssetsFileWriter(filePath + ".mod"))
        {
            bundleInstance.file.Write(writer, bundleReplacers);
        }
        Console.WriteLine("INFO: patching done");
    }

    private static String FindBestTranslation(String tag, TranslationScene scene)
    {
        foreach (var e in scene.entries)
        {
            if (e.tag != tag)
                continue;
            if (e.ru_final != "")
                return e.ru_final;
            if (e.ru_machine != "")
                return e.ru_machine;
            if (e.ru_native != "")
                return e.ru_native;
            if (e.en != "")
                return e.en;
            Console.WriteLine($"WARNING: tag {tag} found but no valid translation present in scene");
            return "";
        }
        Console.WriteLine($"ERROR: Could not find translation entry with tag {tag}");
        throw new ApplicationException("No translation entry");
    }
}

class TranslationEntry
{
    public String tag;
    public String en;
    public String ru_native;
    public String ru_machine;
    public String ru_final;
    public bool verified;
    public String uk;
}

class TranslationScene
{
    public String bundle;
    public String scene;
    public List<TranslationEntry> entries;
}
