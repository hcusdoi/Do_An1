using MovieWinform.Controllers;
using MovieWinform.Models;

namespace MovieWinform.Views;

public partial class MainForm : Form
{
    private readonly MainController _controller;
    private List<Movie> _currentMovies = new();

    public MainForm()
    {
        InitializeComponent();
        _controller = new MainController();
    }

    private async void MainForm_Load(object sender, EventArgs e)
    {
        await LoadMovies("");
    }

    private async Task LoadMovies(string query)
    {
        lblStatus.Text = "Đang tải dữ liệu phim...";
        try {
            _currentMovies = await _controller.SearchMovies(query);
            gridMovies.DataSource = _currentMovies;
            lblStatus.Text = $"Đã tải {_currentMovies.Count} phim.";
        } catch (Exception ex) {
            lblStatus.Text = "Lỗi kết nối tới Server API Python!";
        }
    }

    private async void btnSearch_Click(object sender, EventArgs e)
    {
        await LoadMovies(txtSearch.Text);
    }

    private async void btnRecommend_Click(object sender, EventArgs e)
    {
        int? userId = null;
        int? movieId = null;

        if (int.TryParse(txtUserId.Text, out int uid))
        {
            userId = uid;
        }

        if (gridMovies.SelectedRows.Count > 0)
        {
            movieId = (int)gridMovies.SelectedRows[0].Cells["MovieId"].Value;
        }

        if (userId == null && movieId == null)
        {
            MessageBox.Show("Vui lòng nhập User ID hoặc chọn một bộ phim từ danh sách để lấy thông tin Cold-Start!", "Cảnh báo", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }

        lblStatus.Text = "Đang tìm kiếm gợi ý...";
        try {
            var recommendations = await _controller.GetRecommendations(userId, movieId);
            gridRecommendations.DataSource = recommendations;
            lblStatus.Text = $"Tìm thấy {recommendations.Count} gợi ý.";
        } catch (Exception ex) {
            lblStatus.Text = "Lỗi API!";
        }
    }
}
