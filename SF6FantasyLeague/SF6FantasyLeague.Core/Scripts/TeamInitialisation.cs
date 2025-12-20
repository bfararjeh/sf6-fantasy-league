using SF6FantasyLeague.Core.Models;
using System.Text.RegularExpressions;

namespace SF6FantasyLeague.Core.Scripts;

public class TeamInitialisation
{
    private readonly int _startingBudget;

    public TeamInitialisation(int startingBudget)
    {
        _startingBudget = startingBudget;
    }

    public Team Initialise(List<Player> availablePlayers, List<string> selectedPlayerIds, string teamName)
    {
        if (selectedPlayerIds.Count != 5)
            throw new InvalidOperationException("A team must have 5 players!");

        var selectedPlayers = availablePlayers
            .Where(p => selectedPlayerIds.Contains(p.PlayerID))
            .ToList();

        if (selectedPlayers.Count != 5)
            throw new InvalidOperationException("One or more chosen players are invalid!");

        
        teamName = string.IsNullOrWhiteSpace(teamName) ? "My Team" : teamName.Trim();

        if (!Regex.IsMatch(teamName, @"^[a-zA-Z0-9 ]+$"))
            throw new InvalidOperationException("Team name can only contain letters, numbers, and spaces!");

        if (teamName.Length > 25)
            throw new InvalidOperationException("Team name cannot exceed 25 characters!");


        int totalPrice = selectedPlayers.Sum(p => p.Price);
        if (totalPrice > _startingBudget)
            throw new InvalidOperationException($"Selected players exceed the budget of {_startingBudget}. Your team is worth {totalPrice}!");


        return new Team
        {
            TeamID = Guid.NewGuid().ToString(),
            Name = teamName,
            Players = selectedPlayers,
            LastUpdated = DateTime.UtcNow,
            TeamVersion = 1,
            Score = 0
        };
    }
}