import { createRoot } from "react-dom/client";

import { Access } from "./features/identity/Access";
import "./styles.css";

const token = new URLSearchParams(window.location.hash.slice(1)).get("verificar");
if (token !== null) {
  history.replaceState(null, "", location.pathname + location.search);
}
createRoot(document.getElementById("root")!).render(<Access verificationToken={token} />);
