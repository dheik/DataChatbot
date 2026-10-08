import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import type { AskResponse, Pokemon } from '../api';
import { colors, fonts, regionNames, typeNames } from '../theme';
import PokemonCard from './PokemonCard';

const cell = (v: unknown) => {
  if (v == null) return '—';
  const t = String(v);
  return typeNames[t] || regionNames[t] || t;
};

type Props = { data: AskResponse; width: number; onOpen: (p: Pokemon) => void };

export default function AnswerBlock({ data, width, onOpen }: Props) {
  const [showSql, setShowSql] = useState(false);
  const columns = width >= 700 ? 3 : width >= 440 ? 2 : 1;
  const gap = 12;
  const cardWidth = Math.floor((width - gap * (columns - 1)) / columns);

  return (
    <View style={styles.wrap}>
      <Text style={styles.answer}>{data.answer}</Text>

      {data.result_type === 'pokemon' && (
        <View style={[styles.grid, { gap }]}>
          {data.pokemon.map((p, i) => (
            <PokemonCard key={p.id} pokemon={p} rank={i + 1} width={cardWidth} onPress={() => onOpen(p)} />
          ))}
        </View>
      )}

      {data.result_type === 'table' && data.table && data.table.rows.length > 0 && (
        <ScrollView horizontal style={styles.table}>
          <View>
            <View style={[styles.tr, styles.thead]}>
              {data.table.columns.map((c) => <Text key={c} style={[styles.td, styles.th]}>{c}</Text>)}
            </View>
            {data.table.rows.map((r, i) => (
              <View key={i} style={styles.tr}>
                {data.table!.columns.map((c) => <Text key={c} style={styles.td}>{cell(r[c])}</Text>)}
              </View>
            ))}
          </View>
        </ScrollView>
      )}

      {data.truncated && <Text style={styles.meta}>Mostrando os primeiros {data.row_count} resultados.</Text>}

      <Pressable onPress={() => setShowSql((s) => !s)} accessibilityRole="button" style={styles.sqlToggle}>
        <Text style={styles.sqlToggleText}>{showSql ? 'Ocultar consulta' : 'Ver a consulta usada'}</Text>
        <Text style={styles.meta}>
          {data.row_count} {data.row_count === 1 ? 'resultado' : 'resultados'} em {(data.elapsed_ms / 1000).toFixed(1)} s
          {data.cached ? ', do cache' : ''}
        </Text>
      </Pressable>

      {showSql && (
        <View style={styles.screen}>
          {!!data.explanation && <Text style={styles.screenNote}>{data.explanation}</Text>}
          <Text style={styles.sql} selectable>{data.sql}</Text>
          <Text style={styles.screenNote}>
            Gerada pelo Gemini{data.model ? ` (${data.model})` : ''}{data.self_corrected ? ', corrigida automaticamente após erro' : ''}.
            Os resultados vêm direto do banco.
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: 12 },
  answer: { fontFamily: fonts.body, fontSize: 16, lineHeight: 24, color: colors.ink, maxWidth: 640 },
  grid: { flexDirection: 'row', flexWrap: 'wrap' },
  table: { borderWidth: 1, borderColor: colors.line, borderRadius: 12, backgroundColor: colors.card },
  tr: { flexDirection: 'row', borderBottomWidth: 1, borderColor: colors.paper },
  thead: { backgroundColor: colors.paper },
  td: { fontFamily: fonts.body, fontSize: 14, color: colors.ink, paddingVertical: 8, paddingHorizontal: 12, minWidth: 120 },
  th: { fontFamily: fonts.bodyBold },
  sqlToggle: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: 8 },
  sqlToggleText: { fontFamily: fonts.bodyBold, fontSize: 14, color: colors.red, textDecorationLine: 'underline' },
  meta: { fontFamily: fonts.body, fontSize: 13, color: colors.slate },
  screen: { backgroundColor: colors.screen, borderRadius: 12, padding: 14, gap: 10 },
  sql: { fontFamily: fonts.mono, fontSize: 13, lineHeight: 20, color: colors.screenText },
  screenNote: { fontFamily: fonts.body, fontSize: 12, color: '#93A4B8' },
});
