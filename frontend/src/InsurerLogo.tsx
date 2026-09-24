import { useState } from "react";
import { findInsurerBrand } from "./insurers";

export function InsurerLogo({ insurer }: { insurer: string }) {
  const brand = findInsurerBrand(insurer);
  const [failedSource, setFailedSource] = useState<string | null>(null);
  if (!brand || brand.logo === failedSource) return null;
  return (
    <span className={`insurer-logo insurer-logo--${brand.id}`}>
      <img
        src={brand.logo}
        alt={`לוגו ${brand.name}`}
        width="76"
        height="36"
        decoding="async"
        onError={() => setFailedSource(brand.logo)}
      />
    </span>
  );
}
