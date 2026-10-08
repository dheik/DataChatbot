export const colors = {
  paper: '#EEF1F4',
  card: '#FFFFFF',
  ink: '#1A2230',
  slate: '#5B6676',
  line: '#D3DAE2',
  red: '#C8102E',
  redDark: '#9E0C24',
  screen: '#1F2B3A',
  screenText: '#CFE3D4',
};

export const fonts = {
  display: 'ChakraPetch_700Bold',
  displayMedium: 'ChakraPetch_600SemiBold',
  body: 'IBMPlexSans_400Regular',
  bodyMedium: 'IBMPlexSans_500Medium',
  bodyBold: 'IBMPlexSans_600SemiBold',
  mono: 'IBMPlexMono_400Regular',
};

// Cores oficiais dos tipos
export const typeColors: Record<string, string> = {
  normal: '#9FA19F', fire: '#E62829', water: '#2980EF', grass: '#3FA129', electric: '#FAC000',
  ice: '#3DCEF3', fighting: '#FF8000', poison: '#9141CB', ground: '#915121', flying: '#81B9EF',
  psychic: '#EF4179', bug: '#91A119', rock: '#AFA981', ghost: '#704170', dragon: '#5060E1',
  dark: '#624D4E', steel: '#60A1B8', fairy: '#EF70EF',
};

export const typeNames: Record<string, string> = {
  normal: 'Normal', fire: 'Fogo', water: 'Água', grass: 'Planta', electric: 'Elétrico', ice: 'Gelo',
  fighting: 'Lutador', poison: 'Venenoso', ground: 'Terrestre', flying: 'Voador', psychic: 'Psíquico',
  bug: 'Inseto', rock: 'Pedra', ghost: 'Fantasma', dragon: 'Dragão', dark: 'Sombrio', steel: 'Aço', fairy: 'Fada',
};

export const statLabels: [string, string][] = [
  ['hp', 'HP'], ['attack', 'Ataque'], ['defense', 'Defesa'],
  ['sp_attack', 'Atq. Esp.'], ['sp_defense', 'Def. Esp.'], ['speed', 'Velocidade'],
];

export const regionNames: Record<string, string> = {
  kanto: 'Kanto', johto: 'Johto', hoenn: 'Hoenn', sinnoh: 'Sinnoh', unova: 'Unova', kalos: 'Kalos',
  alola: 'Alola', galar: 'Galar', hisui: 'Hisui', paldea: 'Paldea',
};
