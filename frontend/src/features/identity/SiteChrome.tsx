import { useRef, useState } from "react";

import logo from "../../assets/buzon-xpress-icono.jpeg";

export function Brand() {
  return <span className="buzon-wordmark">
    <img className="buzon-brand-mark" src={logo} width="330" height="218" alt="" />
    <span className="buzon-wordmark-copy">
      <span>BUZON <span className="buzon-wordmark-accent">Xpress</span></span>
      <small>Custodia temporal</small>
    </span>
  </span>;
}

const publicLinks = [
  ["/#como-funciona", "Cómo funciona"],
  ["/#puntos", "Puntos y tarifas"],
  ["/#seguimiento", "Seguimiento"],
  ["/#conocenos", "Conócenos"],
  ["/#contacto", "Contacto"],
];

export function PublicHeader({ focused, signedIn }: { focused?: boolean; signedIn?: boolean }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuButton = useRef<HTMLButtonElement>(null);

  return <header className="public-topbar" onKeyDown={(event) => {
    if (event.key === "Escape" && menuOpen && menuButton.current?.getClientRects().length) {
      event.preventDefault();
      setMenuOpen(false);
      menuButton.current.focus();
    }
  }}>
    <div className="public-layout public-topbar-inner">
      <a className="public-brand-link" href="/" aria-label="BUZON Xpress, inicio"><Brand /></a>
      {!focused && <>
        <button type="button" className="public-menu-toggle" ref={menuButton} aria-expanded={menuOpen}
          aria-controls="public-navigation" onClick={() => setMenuOpen((open) => !open)}>
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"
            strokeLinecap="round" aria-hidden="true">
            <path d={menuOpen ? "m6 6 12 12M18 6 6 18" : "M4 6h16M4 12h16M4 18h16"} />
          </svg>
          {menuOpen ? "Cerrar" : "Menú"}
        </button>
        <nav id="public-navigation" aria-label="Navegación pública" className="public-nav" data-open={menuOpen}>
          {publicLinks.map(([href, label]) => <a key={href} href={href} onClick={() => setMenuOpen(false)}>{label}</a>)}
          <a className="public-nav-action" href={signedIn ? "/cuenta" : "/acceso"}>
            {signedIn ? "Mi cuenta" : "Iniciar sesión"}
          </a>
        </nav>
      </>}
    </div>
  </header>;
}

export function SiteFooter() {
  return <footer className="public-footer" id="contacto">
    <div className="public-layout">
      <div className="public-footer-inner">
        <div>
          <a className="public-brand-link" href="/" aria-label="BUZON Xpress, inicio"><Brand /></a>
          <h2>Nosotros</h2>
          <p>Coordinamos el intercambio de objetos mediante custodia temporal en puntos atendidos.</p>
          <a href="/#conocenos">Nuestra misión y visión <span aria-hidden="true">→</span></a>
        </div>
        <div>
          <h2>Atención y contacto</h2>
          <p>Consulta al personal del punto sobre recepción, retiro e incidencias.</p>
          <p><strong>Correo de referencia</strong><br />atencion@buzonxpress.example</p>
        </div>
        <div>
          <h2>Ubicaciones y horarios</h2>
          <p>Puntos de referencia en La Paz y El Alto. Atención de lunes a sábado según el horario de cada punto.</p>
          <a href="/#puntos">Ver ubicaciones y horarios <span aria-hidden="true">→</span></a>
        </div>
        <div>
          <h2>Avisos del servicio</h2>
          <p>El prerregistro no reserva espacio. El operador confirma la capacidad y el importe al recibir el objeto.</p>
          <p>El seguimiento público solo muestra el estado, el punto y su horario.</p>
        </div>
      </div>
      <div className="public-footer-bottom">
        <p>© BUZON Xpress</p>
        <p>El correo y las ubicaciones son datos ilustrativos.</p>
      </div>
    </div>
  </footer>;
}
