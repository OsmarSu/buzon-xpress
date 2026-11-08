import { createRoot } from "react-dom/client";

import { Access } from "./features/identity/Access";
import "./styles.css";

const params = new URLSearchParams(location.hash.slice(1));
const links = {
  verificationToken: params.get("verificar"),
  resetToken: params.get("recuperar") ?? params.get("restablecer"),
  initialReference: params.get("referencia"),
  initialCustody: params.get("custodia"),
};
if (Object.values(links).some((value) => value !== null)) {
  history.replaceState(null, "", location.pathname + location.search);
}
createRoot(document.getElementById("root")!).render(<Access {...links} />);
