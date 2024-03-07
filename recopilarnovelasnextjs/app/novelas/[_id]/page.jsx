import React from "react";

export default function page({ params }) {
  const { _id } = params;
  return <h1>{_id}</h1>;
}
