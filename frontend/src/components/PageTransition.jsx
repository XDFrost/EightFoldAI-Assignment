import TransitionCurtain from './TransitionCurtain';

const PageTransition = ({ children }) => {
    return (
        <>
            <TransitionCurtain />
            {children}
        </>
    );
};

export default PageTransition;
