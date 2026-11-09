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

export function PublicHeader({ focused, signedIn }: { focused?: boolean; signedIn?: boolean }) {
  return <header className="public-topbar">
    <div className="public-layout public-topbar-inner">
      <a className="public-brand-link" href="/" aria-label="BUZON Xpress, inicio"><Brand /></a>
      {!focused && <>
        <nav aria-label="Navegación pública" className="public-nav">
          <a href="/#como-funciona">Cómo funciona</a>
          <a href="/#puntos">Puntos y tarifas</a>
          <a href="/#seguimiento">Seguimiento</a>
          <a href="/#conocenos">Conócenos</a>
          <a href="/#contacto">Contacto</a>
        </nav>
        <a className="public-nav-action" href={signedIn ? "/cuenta" : "/acceso"}>
          {signedIn ? "Mi cuenta" : "Iniciar sesión"}
        </a>
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
