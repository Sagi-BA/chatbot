function reloadPage() {
  window.sessionStorage.setItem("clear_uploader", "true");
  window.location.reload();
}

function copyToClipboard(textAreaId) {
  alert("copyToClipboard");
  const el = document.getElementById(textAreaId);
  if (el) {
    el.select();
    document.execCommand("copy");
  }
}

function setTextareaValue(key, value) {
  alert("sagi");
  const textarea = document.getElementById(key);
  textarea.value = value;
}

window.addEventListener("load", function () {
  if (window.sessionStorage.getItem("clear_uploader") === "true") {
    window.sessionStorage.removeItem("clear_uploader");
    const fileInput =
      window.parent.document.querySelector('input[type="file"]');
    if (fileInput) {
      fileInput.value = "";
      const event = new Event("change", { bubbles: true });
      fileInput.dispatchEvent(event);
    }
  }
});
