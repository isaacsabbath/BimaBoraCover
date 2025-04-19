import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

// Set page title
document.title = "BimaBora - Affordable Health & Dental Insurance";

// Add meta description
const metaDescription = document.createElement("meta");
metaDescription.name = "description";
metaDescription.content = "BimaBora provides affordable health and dental insurance for low-income Kenyans with flexible payment options.";
document.head.appendChild(metaDescription);

createRoot(document.getElementById("root")!).render(<App />);
