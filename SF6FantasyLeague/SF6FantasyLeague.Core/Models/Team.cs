namespace SF6FantasyLeague.Core.Models;

public class Team
{
    public string TeamID { get; set; }
    public string Name { get; set; }
    public List<Player> Players { get; set; } = new List<Player>();
    public DateTime LastUpdated { get; set; }
    public int TeamVersion { get; set; }
    public int Score { get; set; }
}