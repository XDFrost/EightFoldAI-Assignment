import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import anime from 'animejs';
import { ArrowRight } from 'lucide-react';
import veritasIcon from '../assets/veritas-nobg.svg';

const Landing = () => {
    const navigate = useNavigate();

    useEffect(() => {
        anime({
            targets: '.hero-text',
            opacity: [0, 1],
            translateY: [20, 0],
            delay: anime.stagger(100),
            easing: 'easeOutExpo',
            duration: 1000
        });

        anime({
            targets: '.cta-button',
            scale: [0.9, 1],
            opacity: [0, 1],
            delay: 600,
            easing: 'easeOutElastic(1, .6)'
        });
    }, []);

    return (
        <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center relative overflow-hidden">
            {/* Background Gradient */}
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-gray-800 via-gray-950 to-black opacity-50 z-0"></div>

            {/* Content */}
            <div className="z-10 text-center px-4 max-w-4xl">
                <div className="flex items-center justify-center gap-2 mb-6 hero-text opacity-0">
                    <img src={veritasIcon} alt="Veritas" className="w-10 h-10" />
                    <h1 className="text-5xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                        Veritas
                    </h1>
                </div>

                <p className="text-xl text-gray-400 mb-12 max-w-2xl mx-auto hero-text opacity-0 leading-relaxed">
                    Your intelligent research partner. Veritas combines deep web search with strategic planning to deliver actionable insights in seconds.
                </p>

                <button
                    onClick={() => navigate('/login')}
                    className="cta-button opacity-0 group relative inline-flex items-center gap-3 px-8 py-4 bg-white text-black rounded-full font-semibold text-lg hover:bg-gray-100 transition-all shadow-[0_0_40px_-10px_rgba(255,255,255,0.3)] hover:shadow-[0_0_60px_-15px_rgba(255,255,255,0.5)]"
                >
                    Get Started
                    <ArrowRight className="group-hover:translate-x-1 transition-transform" size={20} />
                </button>
            </div>

            {/* Footer */}
            <div className="absolute bottom-8 text-gray-600 text-sm">
                &copy; {new Date().getFullYear()} EightFold AI. All rights reserved.
            </div>
        </div>
    );
};

export default Landing;
