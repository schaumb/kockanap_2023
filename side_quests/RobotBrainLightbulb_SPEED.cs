public class Task
{
    public int index;
    public int from;
    public int diff;

    public Task(int ix, int i, int to1)
    {
        index = ix;
        from = i;
        diff = to1;
    }
}

public class RobotBrainLightbulb_SPEED
{
    private PriorityQueue<Task, int> _reachableTasks = new();
    private SortedDictionary<int, List<Task>> _unreachableTasks = new();
    
    public static void Main()
    {
        var theObject = new RobotBrainLightbulb_SPEED();
        var num = Int32.Parse(Console.ReadLine());

        for (var i = 0; i < num; ++i)
        {
            var splitted = Console.ReadLine().Split(',');
            var from = Int32.Parse(splitted[0]);
            var to = Int32.Parse(splitted[1]);

            if (!theObject._unreachableTasks.ContainsKey(from))
            {
                theObject._unreachableTasks.Add(from, new List<Task>());
            }
            theObject._unreachableTasks[from].Add(new Task(i, from, to));
        }

        var time = -1;
        var theFirst = true;
        while (theObject._unreachableTasks.Count + theObject._reachableTasks.Count > 0)
        {
            while (theObject._reachableTasks.Count == 0 || 
                   theObject._unreachableTasks.FirstOrDefault(new KeyValuePair<int, List<Task>>(time+1, null!)).Key <= time)
            {
                var first = theObject._unreachableTasks.First();
                
                time = int.Max(time, first.Key);
                
                foreach (var listElem in first.Value)
                {
                    theObject._reachableTasks.Enqueue(listElem, listElem.diff);
                }

                theObject._unreachableTasks.Remove(first.Key);
            }

            var doTask = theObject._reachableTasks.Dequeue();
            if (theFirst)
                theFirst = false;
            else 
                Console.Write(',');
            Console.Write(doTask.index);

            time += doTask.diff;

        }
        Console.WriteLine();
    }  
}  

