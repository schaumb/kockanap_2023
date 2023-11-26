
var line = Console.ReadLine().Trim().ToCharArray();

var was_incremention = false;
for (var i = 1; i < line.Length; ++i)
{
    if (line[i - 1] > line[i])
    {
        var current = line[i - 1];
        for (var j = i; j < line.Length; ++j)
        {
            line[j] = current;
        }

        was_incremention = true;
        break;
    }
}

if (!was_incremention)
{
    var position = line.Length;
    while (position > 0 && line[position - 1] == '9')
    {
        position -= 1;
    }

    if (position == 0)
    {
        char[] newValues = new char[line.Length + 1];
        newValues[0] = '0';
        Array.Copy(line, 0, newValues, 1, line.Length); // copy the old values
        line = newValues;
        ++position;
    }

    var to = ++line[position - 1];

    for (var i = position; i < line.Length; ++i)
    {
        line[i] = to;
    }
}

Console.WriteLine(line);
