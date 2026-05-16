using System.Net.Http.Json;
using System.Text.Json;

namespace MovieWinform.Models;

public class ApiClient
{
    private readonly HttpClient _client;
    private const string BaseUrl = "http://127.0.0.1:8000";

    public ApiClient()
    {
        _client = new HttpClient();
    }

    public async Task<List<Movie>> GetMoviesAsync(string query = "")
    {
        try
        {
            var url = $"{BaseUrl}/movies";
            if (!string.IsNullOrEmpty(query))
                url += $"?query={Uri.EscapeDataString(query)}";
                
            return await _client.GetFromJsonAsync<List<Movie>>(url) ?? new List<Movie>();
        }
        catch (Exception ex)
        {
            Console.WriteLine(ex.Message);
            return new List<Movie>();
        }
    }

    public async Task<List<Movie>> GetRecommendationsAsync(int? userId, int? movieId, int topN = 10)
    {
        try
        {
            var url = $"{BaseUrl}/recommend?top_n={topN}";
            if (userId.HasValue) url += $"&user_id={userId.Value}";
            if (movieId.HasValue) url += $"&movie_id={movieId.Value}";

            return await _client.GetFromJsonAsync<List<Movie>>(url) ?? new List<Movie>();
        }
        catch (Exception ex)
        {
            Console.WriteLine(ex.Message);
            return new List<Movie>();
        }
    }
}
