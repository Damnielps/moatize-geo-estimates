import { useI18n } from "../lib/i18n.jsx";

const CENSITARIOS = [1997, 2007, 2017];

export default function SliderTemporal({ ano, anos, onChange }) {
  const { t } = useI18n();
  const min = anos[0];
  const max = anos[anos.length - 1];
  return (
    <div className="mapa-slider-bar">
      <label htmlFor="slider-ano" style={{ fontWeight: 600, fontSize: 12 }}>
        {t("ano")}
      </label>
      <input
        id="slider-ano"
        type="range"
        min={min}
        max={max}
        step={5}
        list="marcadores-censo"
        value={ano}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-valuetext={String(ano)}
      />
      <datalist id="marcadores-censo">
        {CENSITARIOS.map((c) => (
          <option key={c} value={c} label={String(c)} />
        ))}
      </datalist>
      <span className="mapa-slider-ano">{ano}</span>
    </div>
  );
}
