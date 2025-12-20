namespace SF6FantasyLeague.Core.Models;

public class User
{
    public string UserId { get; set; }
    public string Username { get; set; }
    public string PasswordHash { get; set; }
    public Team? Team { get; set; } = new Team();
}