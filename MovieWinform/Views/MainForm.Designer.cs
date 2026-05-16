namespace MovieWinform.Views;

partial class MainForm
{
    private System.ComponentModel.IContainer components = null;

    protected override void Dispose(bool disposing)
    {
        if (disposing && (components != null))
        {
            components.Dispose();
        }
        base.Dispose(disposing);
    }

    private void InitializeComponent()
    {
        this.gridMovies = new System.Windows.Forms.DataGridView();
        this.gridRecommendations = new System.Windows.Forms.DataGridView();
        this.txtSearch = new System.Windows.Forms.TextBox();
        this.btnSearch = new System.Windows.Forms.Button();
        this.txtUserId = new System.Windows.Forms.TextBox();
        this.btnRecommend = new System.Windows.Forms.Button();
        this.label1 = new System.Windows.Forms.Label();
        this.label2 = new System.Windows.Forms.Label();
        this.label3 = new System.Windows.Forms.Label();
        this.label4 = new System.Windows.Forms.Label();
        this.lblStatus = new System.Windows.Forms.Label();
        
        ((System.ComponentModel.ISupportInitialize)(this.gridMovies)).BeginInit();
        ((System.ComponentModel.ISupportInitialize)(this.gridRecommendations)).BeginInit();
        this.SuspendLayout();
        
        // txtSearch
        this.txtSearch.Location = new System.Drawing.Point(12, 36);
        this.txtSearch.Name = "txtSearch";
        this.txtSearch.Size = new System.Drawing.Size(262, 27);
        this.txtSearch.TabIndex = 0;
        
        // btnSearch
        this.btnSearch.Location = new System.Drawing.Point(280, 35);
        this.btnSearch.Name = "btnSearch";
        this.btnSearch.Size = new System.Drawing.Size(94, 29);
        this.btnSearch.TabIndex = 1;
        this.btnSearch.Text = "Tìm Phim";
        this.btnSearch.UseVisualStyleBackColor = true;
        this.btnSearch.Click += new System.EventHandler(this.btnSearch_Click);
        
        // gridMovies
        this.gridMovies.ColumnHeadersHeightSizeMode = System.Windows.Forms.DataGridViewColumnHeadersHeightSizeMode.AutoSize;
        this.gridMovies.Location = new System.Drawing.Point(12, 70);
        this.gridMovies.Name = "gridMovies";
        this.gridMovies.RowTemplate.Height = 29;
        this.gridMovies.Size = new System.Drawing.Size(460, 480);
        this.gridMovies.TabIndex = 2;
        this.gridMovies.SelectionMode = System.Windows.Forms.DataGridViewSelectionMode.FullRowSelect;
        this.gridMovies.MultiSelect = false;
        
        // txtUserId
        this.txtUserId.Location = new System.Drawing.Point(490, 36);
        this.txtUserId.Name = "txtUserId";
        this.txtUserId.Size = new System.Drawing.Size(125, 27);
        this.txtUserId.TabIndex = 3;
        
        // btnRecommend
        this.btnRecommend.Location = new System.Drawing.Point(630, 35);
        this.btnRecommend.Name = "btnRecommend";
        this.btnRecommend.Size = new System.Drawing.Size(120, 29);
        this.btnRecommend.TabIndex = 4;
        this.btnRecommend.Text = "Lấy Gợi Ý";
        this.btnRecommend.UseVisualStyleBackColor = true;
        this.btnRecommend.Click += new System.EventHandler(this.btnRecommend_Click);
        
        // gridRecommendations
        this.gridRecommendations.ColumnHeadersHeightSizeMode = System.Windows.Forms.DataGridViewColumnHeadersHeightSizeMode.AutoSize;
        this.gridRecommendations.Location = new System.Drawing.Point(490, 70);
        this.gridRecommendations.Name = "gridRecommendations";
        this.gridRecommendations.RowTemplate.Height = 29;
        this.gridRecommendations.Size = new System.Drawing.Size(550, 480);
        this.gridRecommendations.TabIndex = 5;
        
        // Labels
        this.label1.AutoSize = true;
        this.label1.Location = new System.Drawing.Point(12, 13);
        this.label1.Name = "label1";
        this.label1.Text = "1. Danh sách phim toàn cầu (Tìm kiếm):";
        
        this.label2.AutoSize = true;
        this.label2.Location = new System.Drawing.Point(490, 13);
        this.label2.Name = "label2";
        this.label2.Text = "2. User ID (Bỏ trống nếu là khách):";
        
        this.label3.AutoSize = true;
        this.label3.Location = new System.Drawing.Point(12, 560);
        this.label3.Name = "label3";
        this.label3.Text = "* Chọn 1 bộ phim trong danh sách để làm Dữ Liệu Lịch Sử (Cold-Start Content-Based)";
        this.label3.ForeColor = System.Drawing.Color.Gray;
        
        this.lblStatus.AutoSize = true;
        this.lblStatus.Location = new System.Drawing.Point(490, 560);
        this.lblStatus.Name = "lblStatus";
        this.lblStatus.Text = "Trạng thái: Sẵn sàng kết nối tới Python Backend.";
        this.lblStatus.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Bold);
        
        // MainForm
        this.ClientSize = new System.Drawing.Size(1060, 600);
        this.Controls.Add(this.lblStatus);
        this.Controls.Add(this.label3);
        this.Controls.Add(this.label2);
        this.Controls.Add(this.label1);
        this.Controls.Add(this.gridRecommendations);
        this.Controls.Add(this.btnRecommend);
        this.Controls.Add(this.txtUserId);
        this.Controls.Add(this.gridMovies);
        this.Controls.Add(this.btnSearch);
        this.Controls.Add(this.txtSearch);
        this.Name = "MainForm";
        this.Text = "Hệ Thống Gợi Ý Phim (C# MVC + Python FastAPI)";
        this.Load += new System.EventHandler(this.MainForm_Load);
        
        ((System.ComponentModel.ISupportInitialize)(this.gridMovies)).EndInit();
        ((System.ComponentModel.ISupportInitialize)(this.gridRecommendations)).EndInit();
        this.ResumeLayout(false);
        this.PerformLayout();
    }

    private System.Windows.Forms.DataGridView gridMovies;
    private System.Windows.Forms.DataGridView gridRecommendations;
    private System.Windows.Forms.TextBox txtSearch;
    private System.Windows.Forms.Button btnSearch;
    private System.Windows.Forms.TextBox txtUserId;
    private System.Windows.Forms.Button btnRecommend;
    private System.Windows.Forms.Label label1;
    private System.Windows.Forms.Label label2;
    private System.Windows.Forms.Label label3;
    private System.Windows.Forms.Label label4;
    private System.Windows.Forms.Label lblStatus;
}
