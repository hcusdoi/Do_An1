using MovieWinform.Models;

namespace MovieWinform.Controllers;

public class MainController
{
    private readonly ApiClient _apiClient;

    public MainController()
    {
        _apiClient = new ApiClient();
    }

    public async Task<List<Movie>> SearchMovies(string query)
    {
        return await _apiClient.GetMoviesAsync(query);
    }

    public async Task<List<Movie>> GetRecommendations(int? userId, int? movieId)
    {
        return await _apiClient.GetRecommendationsAsync(userId, movieId, 10);
    }
}
