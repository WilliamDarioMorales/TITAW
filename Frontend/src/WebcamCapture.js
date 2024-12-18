import React, { useRef, useState } from "react";
import axios from "axios";
import { Spinner, Button, Container, Form, Card, Alert } from "react-bootstrap";

const WebcamCapture = () => {
  const videoRef = useRef(null);
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState("");
  const [emotion, setEmotion] = useState("");
  const [loading, setLoading] = useState(false);

  const startWebcam = () => {
    navigator.mediaDevices
      .getUserMedia({ video: true })
      .then((stream) => {
        videoRef.current.srcObject = stream;
      })
      .catch((err) => console.error("Error al acceder a la cámara: ", err));
  };

  const captureAndSend = async () => {
    setLoading(true);
    setStatus("");
    setEmotion("");
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg"));

    const formData = new FormData();
    formData.append("email", email);
    formData.append("image", blob);

    try {
      const response = await axios.post("http://127.0.0.1:5000/authenticate", formData);
      setStatus("Autenticación Exitosa ✅");
      setEmotion(`Emoción Detectada: ${response.data.emotion}`);
    } catch (error) {
      setStatus("Error en la autenticación ❌");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container className="mt-5">
      <Card className="shadow-lg">
        <Card.Header as="h5" className="bg-primary text-white text-center">
          Validación de Identidad
        </Card.Header>
        <Card.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Correo del Estudiante</Form.Label>
              <Form.Control
                type="email"
                placeholder="Ingresa tu correo"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </Form.Group>
            <div className="d-flex justify-content-center mb-3">
              <video
                ref={videoRef}
                autoPlay
                muted
                style={{ width: "100%", maxWidth: "400px", borderRadius: "10px", border: "2px solid #007bff" }}
              ></video>
            </div>
            <div className="text-center mb-3">
              <Button variant="success" className="me-2" onClick={startWebcam}>
                Iniciar Cámara
              </Button>
              <Button variant="primary" onClick={captureAndSend} disabled={loading}>
                {loading ? <Spinner animation="border" size="sm" /> : "Validar Identidad"}
              </Button>
            </div>
          </Form>
          {status && (
            <Alert variant={status.includes("Error") ? "danger" : "success"} className="text-center">
              {status}
            </Alert>
          )}
          {emotion && (
            <Alert variant="info" className="text-center">
              {emotion}
            </Alert>
          )}
        </Card.Body>
      </Card>
    </Container>
  );
};

export default WebcamCapture;
