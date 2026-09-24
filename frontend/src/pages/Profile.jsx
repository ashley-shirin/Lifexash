import { useAuth } from "../context/AuthContext.jsx";

export default function Profile() {
  // ProtectedRoute only renders this page once `user` is loaded, so it is never null here.
  const { user, logout } = useAuth();

  return (
    <section>
      <h1>Profile</h1>
      <dl className="profile">
        <dt>Name</dt>
        <dd>{user.name}</dd>
        <dt>Email</dt>
        <dd>{user.email}</dd>
      </dl>
      <button type="button" onClick={() => logout()}>
        Log out
      </button>
    </section>
  );
}
