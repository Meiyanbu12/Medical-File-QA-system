let uploadedFilenames = [];

    window.onload = function () {
      fetch("http://localhost:5000/uploaded-files", { credentials: "include" })
        .then(res => res.json())
        .then(data => {
          const list = document.getElementById("uploadedFilesList");
          const status = document.getElementById("uploadStatus");
          list.innerHTML = "";
          uploadedFilenames = data.files || [];

          if (uploadedFilenames.length > 0) {
            status.textContent = `✅ ${uploadedFilenames.length} file(s) available.`;
            uploadedFilenames.forEach(file => {
              const li = document.createElement("li");
              li.textContent = file;
              list.appendChild(li);
            });
          } else {
            status.textContent = "📂 No files uploaded yet.";
          }
        })
        .catch(err => {
          console.error("Failed to fetch uploaded files:", err);
          document.getElementById("uploadStatus").textContent = "❌ Failed to fetch uploaded files.";
        });
    };

    function uploadFiles() {
      const input = document.getElementById("fileInput");
      const files = input.files;
      if (!files.length) {
        alert("Please select at least one file!");
        return;
      }

      const formData = new FormData();
      for (let file of files) {
        formData.append("files", file);
      }

      document.getElementById("uploadStatus").textContent = "⏳ Uploading...";
      fetch("http://localhost:5000/upload", {
        method: "POST",
        body: formData,
        credentials: "include"
      })
        .then(res => res.json())
        .then(data => {
          uploadedFilenames = data.uploaded;
          document.getElementById("uploadStatus").textContent = `✅ Uploaded ${uploadedFilenames.length} file(s).`;

          const list = document.getElementById("uploadedFilesList");
          list.innerHTML = "";
          uploadedFilenames.forEach(file => {
            const li = document.createElement("li");
            li.textContent = file;
            list.appendChild(li);
          });

          document.getElementById("fileInput").value = ""; // reset input
        })
        .catch(err => {
          console.error("Upload failed:", err);
          document.getElementById("uploadStatus").textContent = "❌ Upload failed.";
        });
    }

    function askQuestion() {
      const question = document.getElementById("questionInput").value.trim();
      const answerBox = document.getElementById("answerBox");

      if (!question) return alert("Please enter a question.");

      answerBox.innerHTML = "🧠 Thinking...";

      fetch("http://localhost:5000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ question })
      })
        .then(res => res.json())
        .then(data => {
          if (!data.answers || data.answers.length === 0) {
            answerBox.innerHTML = "❌ No relevant files found.";
            return;
          }

          answerBox.innerHTML = `<strong>✅ Answers from ${data.answers.length} file(s):</strong><br><br>`;
          data.answers.forEach(item => {
            answerBox.innerHTML += `
              <div style="border: 1px solid #ccc; padding: 10px;">
                <strong>📄 File:</strong> ${item.filename}<br>
                <strong>📝 Answer:</strong><br>${item.answer}
              </div>
            `;
          });
        })
        .catch(err => {
          console.error("Ask failed:", err);
          answerBox.innerHTML = "❌ Failed to get answer.";
        });
    }
    
function logout() {
  fetch("http://localhost:5000/logout", {
    method: "POST",
    credentials: "include"
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert("✅ Logout was successfully completed!");
        window.location.href = "login.html";
      } else {
        alert("❌ Logout failed.");
      }
    })
    .catch(err => {
      console.error("Logout error:", err);
      alert("Something went wrong.");
    });
}