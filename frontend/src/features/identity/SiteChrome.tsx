import { useEffect, useRef, useState } from "react";

import logo from "../../assets/buzon-xpress-icono.jpeg";

export function Brand({ mark = false }: { mark?: boolean }) {
  return <span className="buzon-wordmark">
    {mark && <img className="buzon-brand-mark" src={logo} width="330" height="218" alt="" />}
    <span className="buzon-wordmark-copy">
      <span>BUZON <span className="buzon-wordmark-accent">Xpress</span></span>
      <small>Custodia temporal</small>
    </span>
  </span>;
}

const publicLinks = [
  ["inicio", "Inicio"],
  ["como-funciona", "Cómo funciona"],
  ["puntos", "Puntos y tarifas"],
  ["seguimiento", "Seguimiento"],
  ["conocenos", "Nosotros"],
  ["contacto", "Contacto"],
] as const;

export function PublicHeader({ focused, signedIn }: { focused?: boolean; signedIn?: boolean }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState("inicio");
  const [scrolled, setScrolled] = useState(false);
  const header = useRef<HTMLElement>(null);
  const menuButton = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const element = header.current;
    if (!element) return;
    const rootStyle = document.documentElement.style;
    const previousHeight = rootStyle.getPropertyValue("--public-header-height");
    const measure = () => {
      const height = element.getBoundingClientRect().height;
      rootStyle.setProperty("--public-header-height", height + "px");
    };
    measure();
    const observer = typeof ResizeObserver === "undefined" ? undefined : new ResizeObserver(measure);
    observer?.observe(element);
    window.addEventListener("resize", measure);
    return () => {
      observer?.disconnect();
      window.removeEventListener("resize", measure);
      if (previousHeight) rootStyle.setProperty("--public-header-height", previousHeight);
      else rootStyle.removeProperty("--public-header-height");
    };
  }, []);

  useEffect(() => {
    let frame = 0;
    const update = () => {
      frame = 0;
      setScrolled(window.scrollY > 12);
      const offset = (header.current?.getBoundingClientRect().height ?? 80) + Math.min(innerHeight * 0.25, 180);
      let current = "inicio";
      for (const [id] of publicLinks) {
        const section = document.getElementById(id);
        if (section && section.getBoundingClientRect().top <= offset) current = id;
      }
      setActiveSection(current);
    };
    const schedule = () => { if (!frame) frame = requestAnimationFrame(update); };
    update();
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    window.addEventListener("hashchange", schedule);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
      window.removeEventListener("hashchange", schedule);
    };
  }, []);

  useEffect(() => {
    if (!menuOpen) return;
    const closeOutside = (event: PointerEvent) => {
      if (event.target instanceof Node && !header.current?.contains(event.target)) setMenuOpen(false);
    };
    document.addEventListener("pointerdown", closeOutside);
    return () => document.removeEventListener("pointerdown", closeOutside);
  }, [menuOpen]);

  return <header className="public-topbar" ref={header} data-scrolled={scrolled} onKeyDown={(event) => {
    if (event.key === "Escape" && menuOpen && menuButton.current?.getClientRects().length) {
      event.preventDefault();
      setMenuOpen(false);
      menuButton.current.focus();
    }
  }}>
    <div className="public-layout public-topbar-inner">
      <a className="public-brand-link" href="/#inicio" aria-label="BUZON Xpress, inicio"><Brand /></a>
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
          {publicLinks.map(([id, label]) => <a key={id} href={"/#" + id}
            aria-current={activeSection === id ? "location" : undefined}
            onClick={() => {
              setActiveSection(id);
              setMenuOpen(false);
              requestAnimationFrame(() => document.getElementById(id)?.focus({ preventScroll: true }));
            }}>{label}</a>)}
          <a className="public-nav-action" href={signedIn ? "/cuenta" : "/acceso"}>
            {signedIn ? "Mi cuenta" : "Iniciar sesión"}
          </a>
        </nav>
      </>}
    </div>
  </header>;
}

export function SiteFooter() {
  return <footer className="public-footer" id="contacto" data-public-section tabIndex={-1} aria-labelledby="contact-heading">
    <div className="public-layout">
      <div className="public-footer-heading" data-reveal>
        <p className="public-eyebrow">06 / Estamos para orientarte</p>
        <h2 id="contact-heading">Contacto</h2>
      </div>
      <div className="public-footer-inner">
        <div>
          <a className="public-brand-link" href="/#inicio" aria-label="BUZON Xpress, inicio"><Brand mark /></a>
          <h3>Un punto de encuentro</h3>
          <p>Coordinamos el intercambio de objetos mediante custodia temporal en puntos atendidos.</p>
          <a href="/#conocenos">Nuestra misión y visión <span aria-hidden="true">→</span></a>
        </div>
        <div>
          <h3>Atención y contacto</h3>
          <p>Consulta al personal del punto sobre recepción, retiro e incidencias.</p>
          <p><strong>Correo de referencia</strong><br />atencion@buzonxpress.example</p>
        </div>
        <div>
          <h3>Ubicaciones y horarios</h3>
          <p>Puntos de referencia en La Paz y El Alto. Atención de lunes a sábado según el horario de cada punto.</p>
          <a href="/#puntos">Ver ubicaciones y horarios <span aria-hidden="true">→</span></a>
        </div>
        <div>
          <h3>Avisos del servicio</h3>
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
