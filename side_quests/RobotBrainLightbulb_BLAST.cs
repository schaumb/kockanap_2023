public class RobotBrainLightbulb_BLAST
{
    private Dictionary<String, List<bool?>> _variables = new();
    private Queue<string> strings;

    public List<bool?> recursively()
    {
        var q = strings.Dequeue();
        if (_variables.TryGetValue(q, out var recursively1))
        {
            return recursively1;
        }

        if (q == "NOT")
        {
            return recursively().ConvertAll(input => input == null ? input : !input);
        }
        var res1 = recursively();
        var res2 = recursively();

        var res = new List<bool?>();
        for (var i = 0; i < res1.Count; ++i)
        {
            if (res1[i] == null || res2[i] == null)
            {
                res.Add(null);
                continue;
            }

            switch (q)
            {
                case "AND":
                    res.Add(res1[i].Value && res2[i].Value);
                    break;
                case "OR":
                    res.Add(res1[i].Value || res2[i].Value);
                    break;
                case "NAND":
                    res.Add(!(res1[i].Value && res2[i].Value));
                    break;
                case "NOR":
                    res.Add(!(res1[i].Value || res2[i].Value));
                    break;
                case "XOR":
                    res.Add(res1[i].Value != res2[i].Value);
                    break;
                case "XNOR":
                    res.Add(res1[i].Value == res2[i].Value);
                    break;
                
            }
        }

        return res;
    }
    public static void Main()
    {
        var instance = new RobotBrainLightbulb_BLAST();
        instance.strings = new Queue<string>(Console.ReadLine().Split(' '));

        var line = Console.ReadLine();
        while (line != "")
        {
            var l = line.Split(' ');

            var x = instance._variables[l[0]] = new List<bool?>();

            for (int i = 0; i < l[1].Length; i += 2)
            {
                var signal = (l[1][i] -'0') * 10 + (l[1][i + 1] - '0');
                if (signal <= 8)
                    x.Add(false);
                else if (signal >= 27)
                    x.Add(true);
                else
                    x.Add(null);
            }
            

            line = Console.ReadLine();
        }

        foreach (var bools in instance.recursively())
        {
            if (bools == null)
                Console.Write('E');
            else
                Console.Write(bools.Value ? 1 : 0);
        }
    }  
}  

