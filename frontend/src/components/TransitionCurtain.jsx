import { motion } from 'framer-motion';

const TransitionCurtain = () => {
    return (
        <>
            <motion.div
                className="fixed inset-0 z-[9999] bg-black origin-bottom"
                initial={{ scaleY: 0 }}
                animate={{ scaleY: 0 }}
                exit={{ scaleY: 1 }}
                transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            />
            <motion.div
                className="fixed inset-0 z-[9999] bg-black origin-top"
                initial={{ scaleY: 1 }}
                animate={{ scaleY: 0 }}
                exit={{ scaleY: 0 }}
                transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            />
        </>
    );
};

export default TransitionCurtain;
