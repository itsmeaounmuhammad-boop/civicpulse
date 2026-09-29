import { NavLink, Outlet } from "react-router-dom";

export function Layout() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>CivicPulse</h1>
        <nav>
          <NavLink to="/" end>
            Submit
          </NavLink>
          <NavLink to="/dashboard">Dashboard</NavLink>
          <NavLink to="/stats">Stats</NavLink>
        </nav>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}