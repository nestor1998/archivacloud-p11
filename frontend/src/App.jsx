import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";
const MAX_SIZE = 100 * 1024 * 1024;

function App() {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [message, setMessage] = useState("");
  const [uploading, setUploading] = useState(false);
  const [fileInputKey, setFileInputKey] = useState(Date.now());

  const loadFiles = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/files`);
      setFiles(response.data.files);
    } catch {
      setMessage("No se pudo cargar el listado de archivos.");
    }
  };

  useEffect(() => {
    loadFiles();
  }, []);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    setMessage("");

    if (!file) return;

    setSelectedFile(file);
  };

  const clearSelectedFile = () => {
    setSelectedFile(null);
    setMessage("");
    setFileInputKey(Date.now());
  };

  const calculateSHA256 = async (file) => {
  const arrayBuffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest("SHA-256", arrayBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));

  return hashArray
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
};

  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage("Debes seleccionar un archivo antes de subir.");
      return;
    }

    const extension = selectedFile.name
      .substring(selectedFile.name.lastIndexOf("."))
      .toLowerCase();

    if (![".mp4", ".mov"].includes(extension)) {
      setMessage("Archivo inválido. Solo se permiten archivos MP4 o MOV.");
      return;
    }

    if (selectedFile.size <= 0) {
      setMessage("El archivo no puede estar vacío.");
      return;
    }

    if (selectedFile.size > MAX_SIZE) {
      setMessage("El archivo supera el máximo permitido de 100 MB.");
      return;
    }

    try {
      setUploading(true);
      setMessage("Calculando hash SHA-256...");

      const fileHash = await calculateSHA256(selectedFile);

      setMessage("Solicitando URL firmada...");

      const fileType = selectedFile.name.toLowerCase().endsWith(".mov")
        ? "video/quicktime"
        : "video/mp4";

      const response = await axios.post(`${API_URL}/api/upload/presigned-url`, {
        fileName: selectedFile.name,
        fileType,
        fileSize: selectedFile.size,
        fileHash,
      });

      await axios.put(response.data.presignedUrl, selectedFile, {
        headers: {
          "Content-Type": fileType,
          "x-amz-meta-sha256": fileHash,
        },
      });

      setMessage("Archivo subido correctamente.");
      setSelectedFile(null);
      setFileInputKey(Date.now());
      await loadFiles();
    } catch {
      setMessage("No se pudo subir el archivo.");
    } finally {
      setUploading(false);
    }
  };
  const handleDelete = async (key) => {
    const confirmDelete = window.confirm(
      "¿Seguro que deseas eliminar este archivo?"
    );

    if (!confirmDelete) return;

    try {
      await axios.delete(`${API_URL}/api/files/${encodeURIComponent(key)}`);
      setMessage("Archivo eliminado correctamente.");
      await loadFiles();
    } catch {
      setMessage("No se pudo eliminar el archivo.");
    }
  };

  return (
    <main className="container">
      <h1>ArchivaCloud P-11</h1>
      <p>Portal de carga de archivos MP4 y MOV a Amazon S3.</p>

      <section className="card">
        <h2>Subir archivo</h2>

        <input
          key={fileInputKey}
          type="file"
          accept=".mp4,.mov"
          onChange={handleFileChange}
        />

        <button onClick={handleUpload} disabled={uploading}>
          {uploading ? "Subiendo..." : "Subir archivo"}
        </button>

        {selectedFile && (
          <div className="selected-file">
            <span>
              Archivo seleccionado: <strong>{selectedFile.name}</strong>
            </span>

            <button
              type="button"
              className="clear-button"
              onClick={clearSelectedFile}
            >
              X
            </button>
          </div>
        )}

        {message && <p className="message">{message}</p>}
      </section>

      <section className="card">
        <h2>Archivos almacenados</h2>

        {files.length === 0 ? (
          <p>No hay archivos disponibles.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Tamaño</th>
                <th>Fecha</th>
                <th>Acciones</th>
              </tr>
            </thead>

            <tbody>
              {files.map((file) => (
                <tr key={file.key}>
                    <td data-label="Nombre">
                      <div className="file-name">
                        {file.name}
                      </div>

                      <div className="badges">
                        {file.isDuplicateName && (
                          <span className="duplicate-badge">
                            Duplicado por nombre
                          </span>
                        )}

                        {file.isDuplicateHash && (
                          <span className="duplicate-badge hash-badge">
                            Duplicado por hash
                          </span>
                        )}
                      </div>
                    </td>
                      <td data-label="Tamaño">{(file.size / 1024 / 1024).toFixed(2)} MB</td>
                      <td data-label="Fecha">{new Date(file.lastModified).toLocaleString()}</td>
                      <td data-label="Acciones">
                        <a href={file.url} download>Descargar</a>
                        <button onClick={() => handleDelete(file.key)}>Eliminar</button>
                      </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </main>
  );
}

export default App;