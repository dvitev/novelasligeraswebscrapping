'use client'

export default function Iframe({ src, _id}) {
  return (
    <iframe
      id={_id}
      src={src}
      frameBorder={src === "" ? "1" : "0"}
      width="100%"
      height="500px"
      // sandbox="allow-scripts"
      loading="lazy"
      allowFullScreen
    ></iframe>
  );
}
