namespace SF6FantasyLeague.Core.Models;

public class League
{
    public string LeagueID { get; set; }
    public string Name { get; set; }
    public List<User> Users { get; set; } = new List<User>(); 
}
