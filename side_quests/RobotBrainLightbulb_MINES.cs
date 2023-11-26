
var line1 = Console.ReadLine();
var line2 = Console.ReadLine();
var line3 = Console.ReadLine();

var count = line1.Length / 3;

for (var i = 0; i < count; ++i)
{
    if (line1[i * 3 + 1] == ' ') // 4, 1
    {
        if (line2[i*3+1] == '_')
            Console.Write(4);
        else
            Console.Write(1);
    }
    else if (line2[i * 3] == ' ') // 2, 3, 7
    {
        if (line2[i*3+1] == ' ') 
            Console.Write(7);
        else if (line3[i*3] == '|')
            Console.Write(2);
        else
            Console.Write(3);
    } else if (line2[i*3+1] == ' ') // 0
    {
        Console.Write(0);
    } else if (line3[i * 3] == '|') // 8, 6
    {
        if (line2[i*3+2] == ' ')
            Console.Write(6);
        else
            Console.Write(8);
    } else if (line2[i*3+2] == ' ') // 5
        Console.Write(5);
    else
        Console.Write(9);
}
Console.WriteLine();
