import { Image, Pressable, StyleSheet, Text, View } from 'react-native';
import type { Pokemon } from '../api';
import { colors, fonts, statLabels, typeColors, typeNames } from '../theme';

export function TypeChip({ type }: { type: string }) {
  return (
    <View style={[styles.chip, { backgroundColor: typeColors[type] || colors.slate }]}>
      <Text style={styles.chipText}>{typeNames[type] || type}</Text>
    </View>
  );
}

export function StatBar({ label, value, color, compact }: { label: string; value: number; color: string; compact?: boolean }) {
  return (
    <View style={styles.statRow}>
      <Text style={[styles.statLabel, compact && { width: 62, fontSize: 11 }]}>{label}</Text>
      <Text style={[styles.statValue, compact && { fontSize: 11 }]}>{value}</Text>
      <View style={styles.statTrack}>
        <View style={[styles.statFill, { width: `${Math.min(100, (value / 200) * 100)}%`, backgroundColor: color }]} />
      </View>
    </View>
  );
}

export function badgesFor(p: Pokemon): string[] {
  const b: string[] = [];
  if (p.is_legendary) b.push('Lendário');
  if (p.is_mythical) b.push('Mítico');
  if (p.form_category === 'regional') b.push('Forma regional');
  if (p.form_category === 'mega') b.push('Mega');
  if (p.form_category === 'gigantamax') b.push('Gigantamax');
  return b;
}

type Props = { pokemon: Pokemon; rank: number; width: number; onPress: () => void };

export default function PokemonCard({ pokemon: p, rank, width, onPress }: Props) {
  const main = typeColors[p.types[0]] || colors.slate;
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`${p.name}, total ${p.total}. Ver detalhes`}
      style={({ pressed, hovered }: any) => [styles.card, { width }, (pressed || hovered) && styles.cardActive]}
    >
      <View style={[styles.art, { backgroundColor: main + '1F' }]}>
        <Text style={styles.rank}>{rank}</Text>
        <Image source={{ uri: p.sprite_url }} style={styles.sprite} resizeMode="contain" accessibilityIgnoresInvertColors />
        <Text style={styles.number}>Nº {String(p.pokedex_number).padStart(4, '0')}</Text>
      </View>
      <View style={styles.body}>
        <Text style={styles.name} numberOfLines={1}>{p.name}</Text>
        <View style={styles.chips}>{p.types.map((t) => <TypeChip key={t} type={t} />)}</View>
        <View style={styles.totalRow}>
          <Text style={styles.totalLabel}>Total</Text>
          <Text style={styles.total}>{p.total}</Text>
        </View>
        {statLabels.map(([key, label]) => (
          <StatBar key={key} label={label} value={(p as any)[key]} color={main} compact />
        ))}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.line,
    overflow: 'hidden',
  },
  cardActive: { borderColor: colors.ink },
  art: { height: 132, alignItems: 'center', justifyContent: 'center' },
  sprite: { width: 112, height: 112 },
  rank: { position: 'absolute', top: 8, left: 10, fontFamily: fonts.display, fontSize: 18, color: colors.ink },
  number: { position: 'absolute', top: 10, right: 10, fontFamily: fonts.mono, fontSize: 11, color: colors.slate },
  body: { padding: 12, gap: 4 },
  name: { fontFamily: fonts.displayMedium, fontSize: 17, color: colors.ink },
  chips: { flexDirection: 'row', gap: 6, marginBottom: 6 },
  chip: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 999 },
  chipText: { fontFamily: fonts.bodyBold, fontSize: 11, color: '#fff' },
  totalRow: { flexDirection: 'row', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 2 },
  totalLabel: { fontFamily: fonts.body, fontSize: 12, color: colors.slate },
  total: { fontFamily: fonts.display, fontSize: 22, color: colors.ink },
  statRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  statLabel: { fontFamily: fonts.body, fontSize: 13, color: colors.slate, width: 80 },
  statValue: { fontFamily: fonts.bodyMedium, fontSize: 13, color: colors.ink, width: 28, textAlign: 'right' },
  statTrack: { flex: 1, height: 5, borderRadius: 3, backgroundColor: colors.paper, overflow: 'hidden' },
  statFill: { height: '100%', borderRadius: 3 },
});
