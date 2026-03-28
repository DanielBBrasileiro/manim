import themeData from '../../../../assets/brand/theme.json';

// Por padrão, usamos o estado 'dark'. 
// Futuramente o orquestrador pode injetar 'inverted' via props.
const activeState = "dark";
const colors = themeData.brand.color_states[activeState];

export const Theme = {
    colors: {
        background: colors.background, // Usado apenas se não houver vídeo do Manim por baixo
        textPrimary: colors.text_primary,
        textSecondary: colors.text_secondary,
        accent: themeData.brand.color_states.accent.color,
    },
    materials: themeData.brand.materials,
    laws: themeData.laws,
    identity: themeData.brand.identity
};
