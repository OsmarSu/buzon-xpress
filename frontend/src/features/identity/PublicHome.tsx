import { useEffect, useLayoutEffect, useState } from "react";

import androidQr from "../../assets/buzon-xpress-android-qr.png";
import logo from "../../assets/buzon-xpress-logo.jpeg";
import vision from "../../assets/buzon-xpress-vision.jpeg";
import registrationPhoto from "../../assets/servicio-registro.jpg";
import receptionPhoto from "../../assets/servicio-recepcion.jpg";
import pickupPhoto from "../../assets/servicio-retiro.jpg";
import { PublicPoints, PublicTracking } from "../custody/PublicService";
import { PublicHeader, SiteFooter } from "./SiteChrome";

const androidApk = "https://github.com/OsmarSu/buzon-xpress/releases/download/v0.2.5/buzon-xpress-0.2.5-arm64.apk";

function ServiceArt() {
  return <svg className="public-hero-art" viewBox="0 0 400 356" aria-hidden="true" focusable="false" fill="none">
    <defs>
      <linearGradient id="parcel-lid" x1="138" y1="103" x2="334" y2="211" gradientUnits="userSpaceOnUse">
        <stop stopColor="#eef4ff" /><stop offset="1" stopColor="#9fc3ff" />
      </linearGradient>
      <linearGradient id="parcel-front" x1="128" y1="155" x2="235" y2="289" gradientUnits="userSpaceOnUse">
        <stop stopColor="#8eb6ff" /><stop offset="1" stopColor="#4c81e3" />
      </linearGradient>
      <linearGradient id="parcel-side" x1="235" y1="180" x2="339" y2="275" gradientUnits="userSpaceOnUse">
        <stop stopColor="#5079d0" /><stop offset="1" stopColor="#294d9f" />
      </linearGradient>
    </defs>
    <circle cx="246" cy="170" r="138" fill="#0b6bbf" fillOpacity=".18" />
    <circle cx="246" cy="170" r="115" stroke="#a7c6fc" strokeOpacity=".28" />
    <circle cx="246" cy="170" r="154" stroke="#a7c6fc" strokeOpacity=".24" strokeDasharray="3 10" />
    <path d="M21 246c52 0 60-80 127-80s62 139 142 139c41 0 65-37 82-64" stroke="#bdd5ff" strokeOpacity=".77" strokeWidth="2" strokeLinecap="round" strokeDasharray="2 9" />
    <circle cx="28" cy="246" r="7" fill="#a7c7ff" />
    <path d="m91 266 142 71 144-75-144-74-142 78Z" fill="#081f4d" fillOpacity=".65" />
    <path d="m91 251 142 70 144-74-144-74-142 78Z" fill="#2959aa" stroke="#76a8fa" strokeOpacity=".55" />
    <path d="m124 150 108-59 109 59-109 61-108-61Z" fill="url(#parcel-lid)" />
    <path d="m124 150 108 61v96l-108-60v-97Z" fill="url(#parcel-front)" />
    <path d="m232 211 109-61v96l-109 61v-96Z" fill="url(#parcel-side)" />
    <path d="m165 128 26-14 110 59v36l-26 14v-35l-110-60Z" fill="#eef4ff" fillOpacity=".87" />
    <path d="m153 202 44 24v35l-44-25v-34Z" fill="#eff6ff" />
    <path d="m161 216 27 15m-27-7 19 11" stroke="#426cbb" strokeWidth="2" strokeLinecap="round" />
    <path d="m246 285 40-22" stroke="#96b8f7" strokeWidth="2" strokeLinecap="round" />
    <path d="M340 53c0-14 11-25 25-25s25 11 25 25c0 18-25 43-25 43s-25-25-25-43Z" fill="#eff5ff" />
    <circle cx="365" cy="52" r="9" fill="var(--brand-accent)" />
    <path d="M62 115v18m-9-9h18m250-87v14m-7-7h14" stroke="#d9e8ff" strokeWidth="2" strokeLinecap="round" />
  </svg>;
}

function PublicIntro({ signedIn }: { signedIn: boolean }) {
  return <section className="public-chapter public-intro" id="inicio" data-public-section tabIndex={-1} aria-labelledby="intro-heading">
    <div className="public-layout public-intro-content">
      <div className="public-chapter-topline" data-reveal>
        <h2 id="intro-heading">Inicio</h2>
        <span>01 / BUZON Xpress</span>
      </div>
      <div className="public-hero" data-reveal>
    <div className="public-hero-copy">
      <p className="public-eyebrow">Custodia temporal asistida</p>
      <h1>Intercambia objetos en horarios distintos</h1>
      <p className="public-hero-detail">
        Deja el objeto en un punto atendido. Tu destinatario podrá recogerlo después, dentro del horario del punto,
        con un código temporal.
      </p>
      <div className="public-hero-actions">
        <a className="public-hero-link" href={signedIn ? "/cuenta" : "/registro"}>
          {signedIn ? "Ir a mi cuenta" : "Crear cuenta"}
        </a>
        <a className="public-hero-secondary" href="#como-funciona">
          Ver cómo funciona <span aria-hidden="true">↓</span>
        </a>
      </div>
    </div>
        <ServiceArt />
      </div>
      <section className="public-app-download" aria-labelledby="app-download-heading">
        <div>
          <h3 id="app-download-heading">Descarga la app para Android</h3>
          <p>Android ARM de 64 bits · 45 MB</p>
        </div>
        <a className="public-app-download-link" href={androidApk}>Descargar APK</a>
        <img className="public-app-download-qr" src={androidQr} width="490" height="490"
          alt="QR para descargar BUZON Xpress para Android" />
      </section>
      <a href="#como-funciona" className="public-next-section">Descubre el servicio <span aria-hidden="true">↓</span></a>
    </div>
  </section>;
}

function StepPhoto({ src, alt }: { src: string; alt: string }) {
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);
  return <div className="public-step-media" data-ready={ready} data-failed={failed}>
    <img src={src} alt={alt} loading="lazy" decoding="async" width="900" height="1100"
      onLoad={() => setReady(true)} onError={() => { setReady(true); setFailed(true); }} />
    {failed && <span className="public-image-fallback">Imagen del servicio no disponible</span>}
  </div>;
}

function PublicSteps() {
  return <section className="public-chapter public-steps" id="como-funciona" data-public-section tabIndex={-1} aria-labelledby="steps-heading">
    <div className="public-layout public-chapter-content">
      <div className="public-section-intro" data-reveal>
        <p className="public-eyebrow">02 / El recorrido</p>
        <h2 id="steps-heading">Cómo funciona</h2>
      </div>
      <ol className="public-step-list">
        <li data-reveal>
          <StepPhoto src={registrationPhoto} alt="Persona registrando información de un objeto en una computadora" />
          <div className="public-step-caption"><span className="public-step-number" aria-hidden="true">01</span><h3>Registra el objeto</h3></div>
        </li>
        <li data-reveal>
          <StepPhoto src={receptionPhoto} alt="Preparación de un paquete para dejarlo en un punto de recepción" />
          <div className="public-step-caption"><span className="public-step-number" aria-hidden="true">02</span><h3>Déjalo en el punto</h3></div>
        </li>
        <li data-reveal>
          <StepPhoto src={pickupPhoto} alt="Entrega de un paquete entre dos personas" />
          <div className="public-step-caption"><span className="public-step-number" aria-hidden="true">03</span><h3>Retira con un código</h3></div>
        </li>
      </ol>
      <div className="public-service-note" data-reveal>
        <strong>Una visita bien planificada</strong>
        <p>El espacio y el importe se confirman al recibir el objeto.</p>
        <a href="#puntos">Ver puntos y tarifas <span aria-hidden="true">→</span></a>
      </div>
    </div>
  </section>;
}

function PublicAbout() {
  return <section className="public-chapter public-about" id="conocenos" data-public-section tabIndex={-1} aria-labelledby="about-heading">
    <div className="public-layout public-chapter-content">
    <div className="public-section-intro" data-reveal>
      <p className="public-eyebrow">05 / Nuestra razón de ser</p>
      <h2 id="about-heading">Nosotros</h2>
    </div>
    <div className="public-about-grid">
      <article className="public-about-card" data-reveal>
        <img className="public-about-logo" src={logo} alt="BUZON Xpress" width="1052" height="1008" loading="lazy" />
        <div className="public-about-copy">
          <h3>Nuestra misión</h3>
          <p>Facilitar el intercambio de objetos entre personas y pequeños comercios cuando sus horarios no coinciden.</p>
          <p>El personal de cada punto registra la recepción, mantiene el objeto en custodia y verifica el código antes del retiro.</p>
        </div>
      </article>
      <article className="public-about-card" data-reveal>
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
    </div>
  </section>;
}

export function PublicHome({ signedIn, initialReference }: { signedIn: boolean; initialReference: string | null }) {
  useLayoutEffect(() => {
    const frame = requestAnimationFrame(() => document.getElementById(location.hash.slice(1))?.scrollIntoView());
    return () => cancelAnimationFrame(frame);
  }, []);

  useEffect(() => {
    if (!("IntersectionObserver" in window) || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    document.querySelectorAll(".public-home [data-reveal]").forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  }, []);

  return <div className="public-site public-home">
    <a className="buzon-skip" href="#contenido-principal">Saltar al contenido</a>
    <PublicHeader signedIn={signedIn} />
    <main className="public-main" id="contenido-principal" tabIndex={-1}>
      <PublicIntro signedIn={signedIn} />
      <PublicSteps />
      <PublicPoints />
      <PublicTracking initialReference={initialReference} />
      <PublicAbout />
    </main>
    <SiteFooter />
  </div>;
}
