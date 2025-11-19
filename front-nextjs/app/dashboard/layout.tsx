import React from 'react';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div>
      {/* Aquí puedes agregar un sidebar, header, etc. */}
      <header>Dashboard Header</header>
      <main>{children}</main>
    </div>
  );
}