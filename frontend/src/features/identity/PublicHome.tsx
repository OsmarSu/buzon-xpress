import { useLayoutEffect } from "react";

import logo from "../../assets/buzon-xpress-logo.jpeg";
import vision from "../../assets/buzon-xpress-vision.jpeg";
import { PublicPoints, PublicTracking } from "../custody/PublicService";
import { PublicHeader, SiteFooter } from "./SiteChrome";

function PublicIntro({ signedIn, initialReference }: { signedIn: boolean; initialReference: string | null }) {
  return <div className="public-hero">
    <div className="public-layout public-hero-content">
      <p className="public-eyebrow">Custodia temporal asistida</p>
      <h1>Deja un objeto.<br /><span>Que lo recojan después.</span></h1>
      <p className="public-hero-detail">
        Deja el objeto en un punto atendido. Tu destinatario podrá recogerlo después, dentro del horario del punto,
        con un código temporal.
      </p>
      <PublicTracking initialReference={initialReference} />
      <div className="public-hero-actions">
        <a className="public-hero-link" href={signedIn ? "/cuenta" : "/registro"}>
          {signedIn ? "Ir a mi cuenta" : "Crear cuenta"}
        </a>
        <a className="public-hero-secondary" href="#puntos">
          Ver puntos de servicio <span aria-hidden="true">↓</span>
        </a>
      </div>
    </div>
  </div>;
}

function PublicSteps() {
  return <section className="public-steps" id="como-funciona" aria-labelledby="steps-heading">
    <div className="public-section-intro">
      <p className="public-eyebrow">El recorrido</p>
      <h2 id="steps-heading">De la entrega al retiro</h2>
    </div>
    <ol className="public-step-list">
      <li>
        <span className="public-step-number" aria-hidden="true">01</span>
        <h3>Registra el objeto</h3>
        <p>Elige el punto, indica el contacto del destinatario y declara el tamaño. Podrás cancelar antes de depositarlo.</p>
      </li>
      <li>
        <span className="public-step-number" aria-hidden="true">02</span>
        <h3>Déjalo en el punto</h3>
        <p>El operador comprueba la capacidad, confirma el costo y registra el cobro y la ubicación al recibir el objeto.</p>
      </li>
      <li>
        <span className="public-step-number" aria-hidden="true">03</span>
        <h3>Retira con un código</h3>
        <p>El destinatario genera su código temporal. El operador lo verifica y deja constancia de la entrega realizada.</p>
      </li>
    </ol>
    <div className="public-service-note">
      <strong>Antes de ir al punto</strong>
      <p>Consulta el horario y cotiza según el tamaño y el plazo. El espacio se confirma cuando el operador recibe el objeto.</p>
      <a href="#puntos">Consultar puntos <span aria-hidden="true">→</span></a>
    </div>
  </section>;
}

function PublicAbout() {
  return <section className="public-about" id="conocenos" aria-labelledby="about-heading">
    <div className="public-section-intro">
      <p className="public-eyebrow">Conócenos</p>
      <h2 id="about-heading">Nosotros</h2>
    </div>
    <div className="public-about-grid">
      <article className="public-about-card">
        <img className="public-about-logo" src={logo} alt="BUZON Xpress" width="1052" height="1008" loading="lazy" />
        <div className="public-about-copy">
          <h3>Nuestra misión</h3>
          <p>Facilitar el intercambio de objetos entre personas y pequeños comercios cuando sus horarios no coinciden.</p>
          <p>El personal de cada punto registra la recepción, mantiene el objeto en custodia y verifica el código antes del retiro.</p>
        </div>
      </article>
      <article className="public-about-card">
        <figure className="public-about-vision">
          <img src={vision} alt="Ilustración de una futura red de puntos de servicio en Bolivia" width="1200" height="800" loading="lazy" />
          <figcaption>Visión de marca · ilustración conceptual</figcaption>
        </figure>
        <div className="public-about-copy">
          <h3>Nuestra visión</h3>
          <p>Ampliar la red de puntos en Bolivia a medida que se comprueben la demanda y la capacidad de atención.</p>
          <a href="#puntos">Consultar la cobertura actual <span aria-hidden="true">→</span></a>
        </div>
      </article>
    </div>
  </section>;
}

export function PublicHome({ signedIn, initialReference }: { signedIn: boolean; initialReference: string | null }) {
  useLayoutEffect(() => {
    document.getElementById(location.hash.slice(1))?.scrollIntoView();
  }, []);

  return <div className="public-site public-home">
    <a className="buzon-skip" href="#contenido-principal">Saltar al contenido</a>
    <PublicHeader signedIn={signedIn} />
    <main className="public-main" id="contenido-principal" tabIndex={-1}>
      <PublicIntro signedIn={signedIn} initialReference={initialReference} />
      <div className="public-layout public-home-content">
        <PublicSteps />
        <PublicPoints />
        <PublicAbout />
      </div>
    </main>
    <SiteFooter />
  </div>;
}
