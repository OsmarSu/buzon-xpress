import { PublicService } from "../custody/PublicService";
import { PublicHeader, SiteFooter } from "./SiteChrome";

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
  return <div className="public-hero">
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

export function PublicHome({ signedIn, initialReference }: { signedIn: boolean; initialReference: string | null }) {
  return <div className="public-site">
    <a className="buzon-skip" href="#contenido-principal">Saltar al contenido</a>
    <PublicHeader signedIn={signedIn} />
    <main className="public-layout public-main" id="contenido-principal" tabIndex={-1}>
      <PublicIntro signedIn={signedIn} />
      <PublicSteps />
      <PublicService initialReference={initialReference} />
    </main>
    <SiteFooter />
  </div>;
}
