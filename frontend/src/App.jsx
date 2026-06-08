import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [files, setFiles] = useState([]);

  const loadFiles = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/files`);
      setFiles(response.data.files);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    loadFiles();
  }, []);

  return (
    <div className="container">
      <h1>ArchivaCloud P-11</h1>

      <h2>Archivos almacenados</h2>

      {files.length === 0 ? (
        <p>No hay archivos disponibles.</p>
      ) : (
        <ul>
          {files.map((file) => (
            <li key={file.key}>
              {file.name}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default App;