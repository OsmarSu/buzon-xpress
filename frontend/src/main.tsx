import { createRoot } from "react-dom/client";

import { Access } from "./features/identity/Access";
import "./styles.css";

const root = createRoot(document.getElementById("root")!);
let navigation = 0;

function renderLocation(initial = false) {
  const params = new URLSearchParams(location.hash.slice(1));
  const links = {
    verificationToken: params.get("verificar"),
    resetToken: params.get("recuperar") ?? params.get("restablecer"),
    initialReference: params.get("referencia"),
    initialCustody: params.get("custodia"),
  };

  if (location.hash === "#acceso") {
    history.replaceState(null, "", "/acceso");
  } else if (Object.values(links).some((value) => value !== null)) {
    history.replaceState(null, "", location.pathname + location.search);
  } else if (!initial) {
    return;
  }

  root.render(<Access key={++navigation} {...links} />);
}

renderLocation(true);
window.addEventListener("hashchange", () => renderLocation());
