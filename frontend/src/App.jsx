// Importa useEffect y useState desde React
import { useEffect, useState } from "react";

// Importa Axios para hacer peticiones HTTP al backend
import axios from "axios";

// Importa los estilos CSS de la aplicación
import "./App.css";

// URL base del backend FastAPI
const API_URL = "http://127.0.0.1:8000";

// Tamaño máximo permitido para los archivos: 100 MB
const MAX_SIZE = 100 * 1024 * 1024;

// Componente principal de la aplicación
function App() {

  // Estado que almacena la lista de archivos obtenidos desde el backend
  const [files, setFiles] = useState([]);

  // Estado que guarda el archivo seleccionado por el usuario
  const [selectedFile, setSelectedFile] = useState(null);

  // Estado que muestra mensajes informativos o de error en pantalla
  const [message, setMessage] = useState("");

  // Estado que indica si actualmente se está subiendo un archivo
  const [uploading, setUploading] = useState(false);

  // Estado usado para reiniciar el input de archivo cuando se limpia la selección
  const [fileInputKey, setFileInputKey] = useState(Date.now());

  // Función que carga desde el backend la lista de archivos almacenados
  const loadFiles = async () => {
    try {

      // Solicita al backend el listado de archivos
      const response = await axios.get(`${API_URL}/api/files`);

      // Guarda los archivos recibidos en el estado
      setFiles(response.data.files);
    } catch {

      // Muestra mensaje si ocurre un error al cargar archivos
      setMessage("No se pudo cargar el listado de archivos.");
    }
  };

  // Hook que se ejecuta una vez al cargar el componente
  useEffect(() => {

    // Carga los archivos disponibles al iniciar la aplicación
    loadFiles();
  }, []);

  // Función que se ejecuta cuando el usuario selecciona un archivo
  const handleFileChange = (event) => {

    // Obtiene el primer archivo seleccionado
    const file = event.target.files[0];

    // Limpia mensajes anteriores
    setMessage("");

    // Si no se seleccionó archivo, termina la función
    if (!file) return;

    // Guarda el archivo seleccionado en el estado
    setSelectedFile(file);
  };

  // Función para limpiar el archivo seleccionado
  const clearSelectedFile = () => {

    // Elimina el archivo seleccionado del estado
    setSelectedFile(null);

    // Limpia mensajes en pantalla
    setMessage("");

    // Cambia la key del input para reiniciarlo visualmente
    setFileInputKey(Date.now());
  };

  // Función que calcula el hash SHA-256 del archivo seleccionado
  const calculateSHA256 = async (file) => {

    // Convierte el archivo a ArrayBuffer para poder procesarlo
    const arrayBuffer = await file.arrayBuffer();

    // Calcula el hash SHA-256 usando la API Web Crypto
    const hashBuffer = await crypto.subtle.digest("SHA-256", arrayBuffer);

    // Convierte el resultado del hash a un arreglo de bytes
    const hashArray = Array.from(new Uint8Array(hashBuffer));

    // Convierte cada byte a hexadecimal y une todo en un string
    return hashArray
      .map((byte) => byte.toString(16).padStart(2, "0"))
      .join("");
  };

  // Función principal para subir archivos a S3
  const handleUpload = async () => {

    // Verifica que exista un archivo seleccionado
    if (!selectedFile) {
      setMessage("Debes seleccionar un archivo antes de subir.");
      return;
    }

    // Obtiene la extensión del archivo seleccionado
    const extension = selectedFile.name
      .substring(selectedFile.name.lastIndexOf("."))
      .toLowerCase();

    // Valida que la extensión sea MP4 o MOV
    if (![".mp4", ".mov"].includes(extension)) {
      setMessage("Archivo inválido. Solo se permiten archivos MP4 o MOV.");
      return;
    }

    // Valida que el archivo no esté vacío
    if (selectedFile.size <= 0) {
      setMessage("El archivo no puede estar vacío.");
      return;
    }

    // Valida que el archivo no supere los 100 MB
    if (selectedFile.size > MAX_SIZE) {
      setMessage("El archivo supera el máximo permitido de 100 MB.");
      return;
    }

    try {

      // Activa el estado de subida
      setUploading(true);

      // Informa al usuario que se está calculando el hash
      setMessage("Calculando hash SHA-256...");

      // Calcula el hash SHA-256 del archivo
      const fileHash = await calculateSHA256(selectedFile);

      // Informa al usuario que se solicitará la URL firmada
      setMessage("Solicitando URL firmada...");

      // Determina el tipo MIME según la extensión del archivo
      const fileType = selectedFile.name.toLowerCase().endsWith(".mov")
        ? "video/quicktime"
        : "video/mp4";

      // Solicita al backend una URL prefirmada para subir el archivo a S3
      const response = await axios.post(`${API_URL}/api/upload/presigned-url`, {
        fileName: selectedFile.name,
        fileType,
        fileSize: selectedFile.size,
        fileHash,
      });

      // Sube el archivo directamente a S3 usando la URL prefirmada
      await axios.put(response.data.presignedUrl, selectedFile, {
        headers: {
          "Content-Type": fileType,
          "x-amz-meta-sha256": fileHash,
        },
      });

      // Muestra mensaje de éxito
      setMessage("Archivo subido correctamente.");

      // Limpia el archivo seleccionado
      setSelectedFile(null);

      // Reinicia el input de selección de archivo
      setFileInputKey(Date.now());

      // Recarga el listado de archivos almacenados
      await loadFiles();
    } catch {

      // Muestra mensaje si falla la subida
      setMessage("No se pudo subir el archivo.");
    } finally {

      // Desactiva el estado de subida al finalizar
      setUploading(false);
    }
  };

  // Función para eliminar un archivo
  const handleDelete = async (key) => {

    // Solicita confirmación antes de eliminar
    const confirmDelete = window.confirm(
      "¿Seguro que deseas eliminar este archivo?"
    );

    // Si el usuario cancela, no continúa
    if (!confirmDelete) return;

    try {

      // Envía solicitud DELETE al backend usando la key del archivo
      await axios.delete(`${API_URL}/api/files/${encodeURIComponent(key)}`);

      // Muestra mensaje de éxito
      setMessage("Archivo eliminado correctamente.");

      // Recarga la lista de archivos
      await loadFiles();
    } catch {

      // Muestra mensaje si ocurre un error al eliminar
      setMessage("No se pudo eliminar el archivo.");
    }
  };

  // Renderizado principal de la interfaz
  return (
    <main className="container">

      {/* Título principal */}
      <h1>ArchivaCloud P-11</h1>

      {/* Descripción de la aplicación */}
      <p>Portal de carga de archivos MP4 y MOV a Amazon S3.</p>

      {/* Sección para subir archivos */}
      <section className="card">
        <h2>Subir archivo</h2>

        {/* Input para seleccionar archivos MP4 o MOV */}
        <input
          key={fileInputKey}
          type="file"
          accept=".mp4,.mov"
          onChange={handleFileChange}
        />

        {/* Botón para iniciar la subida */}
        <button onClick={handleUpload} disabled={uploading}>
          {uploading ? "Subiendo..." : "Subir archivo"}
        </button>

        {/* Muestra información del archivo seleccionado */}
        {selectedFile && (
          <div className="selected-file">
            <span>
              Archivo seleccionado: <strong>{selectedFile.name}</strong>
            </span>

            {/* Botón para limpiar el archivo seleccionado */}
            <button
              type="button"
              className="clear-button"
              onClick={clearSelectedFile}
            >
              X
            </button>
          </div>
        )}

        {/* Muestra mensajes al usuario */}
        {message && <p className="message">{message}</p>}
      </section>

      {/* Sección que muestra archivos almacenados */}
      <section className="card">
        <h2>Archivos almacenados</h2>

        {/* Si no hay archivos, muestra mensaje */}
        {files.length === 0 ? (
          <p>No hay archivos disponibles.</p>
        ) : (

          // Tabla con los archivos almacenados
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

              {/* Recorre la lista de archivos y crea una fila por cada uno */}
              {files.map((file) => (
                <tr key={file.key}>

                    {/* Columna del nombre del archivo */}
                    <td data-label="Nombre">
                      <div className="file-name">
                        {file.name}
                      </div>

                      {/* Contenedor de etiquetas de duplicados */}
                      <div className="badges">

                        {/* Muestra etiqueta si el archivo está duplicado por nombre */}
                        {file.isDuplicateName && (
                          <span className="duplicate-badge">
                            Duplicado por nombre
                          </span>
                        )}

                        {/* Muestra etiqueta si el archivo está duplicado por hash */}
                        {file.isDuplicateHash && (
                          <span className="duplicate-badge hash-badge">
                            Duplicado por hash
                          </span>
                        )}
                      </div>
                    </td>

                      {/* Columna que muestra el tamaño en MB */}
                      <td data-label="Tamaño">{(file.size / 1024 / 1024).toFixed(2)} MB</td>

                      {/* Columna que muestra la fecha formateada */}
                      <td data-label="Fecha">{new Date(file.lastModified).toLocaleString()}</td>

                      {/* Columna con acciones disponibles */}
                      <td data-label="Acciones">

                        {/* Enlace para descargar archivo */}
                        <a href={file.url} download>Descargar</a>

                        {/* Botón para eliminar archivo */}
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

// Exporta el componente App para ser usado por React
export default App;