import { Image, Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import type { Pokemon } from '../api';
import { colors, fonts, regionNames, statLabels, typeColors } from '../theme';
import { StatBar, TypeChip, badgesFor } from './PokemonCard';

export default function PokemonModal({ pokemon: p, onClose }: { pokemon: Pokemon | null; onClose: () => void }) {
  if (!p) return null;
  const main = typeColors[p.types[0]] || colors.slate;
  const facts: [string, string][] = [
    ['Região', regionNames[p.region] || p.region],
    ['Geração', String(p.generation)],
    ['Altura', `${p.height_m.toLocaleString('pt-BR')} m`],
    ['Peso', `${p.weight_kg.toLocaleString('pt-BR')} kg`],
    ['Taxa de captura', p.capture_rate != null ? String(p.capture_rate) : '—'],
  ];
  const badges = badgesFor(p);

  return (
    <Modal visible transparent animationType="fade" onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose} accessibilityLabel="Fechar detalhes" />
      <View style={styles.sheetWrap} pointerEvents="box-none">
        <View style={styles.sheet}>
          <ScrollView contentContainerStyle={{ paddingBottom: 20 }}>
            <View style={[styles.hero, { backgroundColor: main + '22' }]}>
              <Image source={{ uri: p.sprite_url }} style={styles.sprite} resizeMode="contain" />
            </View>
            <View style={styles.content}>
              <Text style={styles.number}>Nº {String(p.pokedex_number).padStart(4, '0')}</Text>
              <Text style={styles.name}>{p.name}</Text>
              <View style={styles.row}>
                {p.types.map((t) => <TypeChip key={t} type={t} />)}
                {badges.map((b) => <Text key={b} style={styles.badge}>{b}</Text>)}
              </View>

              <Text style={styles.section}>Status base</Text>
              {statLabels.map(([k, label]) => <StatBar key={k} label={label} value={(p as any)[k]} color={main} />)}
              <View style={styles.totalRow}>
                <Text style={styles.totalLabel}>Total</Text>
                <Text style={styles.total}>{p.total}</Text>
              </View>

              <Text style={styles.section}>Habilidades</Text>
              {p.abilities.map((a) => (
                <Text key={a.name} style={styles.text}>{a.name}{a.hidden ? '  (oculta)' : ''}</Text>
              ))}

              <Text style={styles.section}>Ficha</Text>
              {facts.map(([k, v]) => (
                <View key={k} style={styles.fact}>
                  <Text style={styles.factKey}>{k}</Text>
                  <Text style={styles.text}>{v}</Text>
                </View>
              ))}
            </View>
          </ScrollView>
          <Pressable onPress={onClose} style={styles.close} accessibilityRole="button">
            <Text style={styles.closeText}>Fechar</Text>
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(26,34,48,0.55)' },
  sheetWrap: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 16 },
  sheet: { width: '100%', maxWidth: 440, maxHeight: '92%', backgroundColor: colors.card, borderRadius: 18, overflow: 'hidden' },
  hero: { height: 200, alignItems: 'center', justifyContent: 'center' },
  sprite: { width: 180, height: 180 },
  content: { paddingHorizontal: 20, paddingTop: 14, gap: 6 },
  number: { fontFamily: fonts.mono, fontSize: 12, color: colors.slate },
  name: { fontFamily: fonts.display, fontSize: 28, color: colors.ink },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, alignItems: 'center' },
  badge: { fontFamily: fonts.bodyMedium, fontSize: 12, color: colors.ink, borderWidth: 1, borderColor: colors.line, borderRadius: 999, paddingHorizontal: 8, paddingVertical: 1 },
  section: { fontFamily: fonts.displayMedium, fontSize: 16, color: colors.ink, marginTop: 14 },
  totalRow: { flexDirection: 'row', justifyContent: 'space-between', borderTopWidth: 1, borderColor: colors.line, paddingTop: 6, marginTop: 4 },
  totalLabel: { fontFamily: fonts.bodyMedium, color: colors.slate },
  total: { fontFamily: fonts.display, fontSize: 20, color: colors.ink },
  text: { fontFamily: fonts.body, fontSize: 14, color: colors.ink },
  fact: { flexDirection: 'row', justifyContent: 'space-between' },
  factKey: { fontFamily: fonts.body, fontSize: 14, color: colors.slate },
  close: { backgroundColor: colors.ink, paddingVertical: 14, alignItems: 'center' },
  closeText: { fontFamily: fonts.bodyBold, color: '#fff', fontSize: 15 },
});
