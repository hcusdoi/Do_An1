using System.Text.Json.Serialization;

namespace MovieWinform.Models;

public class Movie
{
    [JsonPropertyName("movieId")]
    public int MovieId { get; set; }

    [JsonPropertyName("title")]
    public string Title { get; set; } = string.Empty;

    [JsonPropertyName("genres_clean")]
    public string Genres { get; set; } = string.Empty;

    [JsonPropertyName("Hybrid_Score")]
    public double? HybridScore { get; set; }
    
    [JsonPropertyName("CF_Score")]
    public double? CfScore { get; set; }

    [JsonPropertyName("CBF_Score")]
    public double? CbfScore { get; set; }
}
