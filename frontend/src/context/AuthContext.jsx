import { createContext, useState, useEffect, useContext } from 'react';
import { getCurrentUser, login, signup, logout } from '../services/authService';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const user = getCurrentUser();
        setUser(user);
        setLoading(false);
    }, []);

    const handleLogin = async (email, password) => {
        const data = await login(email, password);
        setUser(data.user);
        return data;
    };

    const handleSignup = async (email, password) => {
        const data = await signup(email, password);
        setUser(data.user);
        return data;
    };

    const handleLogout = () => {
        logout();
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, login: handleLogin, signup: handleSignup, logout: handleLogout, loading }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
