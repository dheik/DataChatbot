import { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput,
  View, useWindowDimensions,
} from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useFonts } from 'expo-font';
import { ChakraPetch_600SemiBold, ChakraPetch_700Bold } from '@expo-google-fonts/chakra-petch';
import { IBMPlexSans_400Regular, IBMPlexSans_500Medium, IBMPlexSans_600SemiBold } from '@expo-google-fonts/ibm-plex-sans';
import { IBMPlexMono_400Regular } from '@expo-google-fonts/ibm-plex-mono';

import { api, ApiError, AskResponse, Pokemon } from './src/api';
import AnswerBlock from './src/components/AnswerBlock';
import PokemonModal from './src/components/PokemonModal';
import { colors, fonts } from './src/theme';

type Turn =
  | { kind: 'question'; id: string; text: string }
  | { kind: 'answer'; id: string; data: AskResponse }
  | { kind: 'error'; id: string; text: string; question: string };

const FALLBACK_EXAMPLES = [
  'Qual o Pokémon de fogo com os status base mais altos da região de Alola?',
  'Quais os 5 Pokémon mais rápidos que não são lendários?',
  'Quantos Pokémon de cada tipo primário existem?',
];
const MAX_LEN = 300;
const sessionId = Math.random().toString(36).slice(2);

export default function App() {
  const [fontsLoaded] = useFonts({
    ChakraPetch_600SemiBold, ChakraPetch_700Bold,
    IBMPlexSans_400Regular, IBMPlexSans_500Medium, IBMPlexSans_600SemiBold, IBMPlexMono_400Regular,
  });
  const { width } = useWindowDimensions();
  const contentWidth = Math.min(width, 860) - 32;

  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [examples, setExamples] = useState<string[]>(FALLBACK_EXAMPLES);
  const [selected, setSelected] = useState<Pokemon | null>(null);
  const scrollRef = useRef<ScrollView>(null);

  useEffect(() => {
    api.examples().then(setExamples).catch(() => {});
  }, []);

  async function ask(raw: string) {
    const question = raw.trim();
    if (question.length < 3 || loading) return;
    const id = String(Date.now());
    setInput('');
    setTurns((t) => [...t, { kind: 'question', id: `q${id}`, text: question }]);
    setLoading(true);
    try {
      const data = await api.ask(question, sessionId);
      setTurns((t) => [...t, { kind: 'answer', id: `a${id}`, data }]);
    } catch (e) {
      const text = e instanceof ApiError ? e.message : 'Algo deu errado ao consultar a API.';
      setTurns((t) => [...t, { kind: 'error', id: `e${id}`, text, question }]);
    } finally {
      setLoading(false);
      setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 80);
    }
  }

  if (!fontsLoaded) {
    return <View style={[styles.root, styles.center]}><ActivityIndicator color={colors.red} /></View>;
  }

  const canSend = input.trim().length >= 3 && !loading;

  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <SafeAreaView style={styles.root} edges={['top', 'bottom']}>
        <View style={styles.header}>
          <View style={[styles.headerInner, { width: contentWidth }]}>
            <View style={styles.lens}><View style={styles.lensGlow} /></View>
            <View style={{ flex: 1 }}>
              <Text style={styles.title}>DataDex</Text>
              <Text style={styles.subtitle}>Pergunte em português. A resposta sai do banco da Pokédex, não da imaginação da IA.</Text>
            </View>
          </View>
        </View>

        <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
          <ScrollView ref={scrollRef} contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
            <View style={{ width: contentWidth, gap: 20 }}>
              {turns.length === 0 && (
                <View style={styles.empty}>
                  <Text style={styles.emptyTitle}>O que você quer descobrir?</Text>
                  <Text style={styles.emptyText}>
                    Tipos, status base, regiões, habilidades, formas regionais e lendários de 1.323 Pokémon e formas.
                    Toque em uma pergunta para começar.
                  </Text>
                  <View style={styles.examples}>
                    {examples.map((ex) => (
                      <Pressable key={ex} onPress={() => ask(ex)} style={({ hovered }: any) => [styles.example, hovered && styles.exampleHover]}>
                        <Text style={styles.exampleText}>{ex}</Text>
                      </Pressable>
                    ))}
                  </View>
                </View>
              )}

              {turns.map((t) => {
                if (t.kind === 'question') {
                  return (
                    <View key={t.id} style={styles.qBubble}>
                      <Text style={styles.qText}>{t.text}</Text>
                    </View>
                  );
                }
                if (t.kind === 'error') {
                  return (
                    <View key={t.id} style={styles.error}>
                      <Text style={styles.errorText}>{t.text}</Text>
                      <Pressable onPress={() => ask(t.question)} accessibilityRole="button">
                        <Text style={styles.retry}>Tentar de novo</Text>
                      </Pressable>
                    </View>
                  );
                }
                return <AnswerBlock key={t.id} data={t.data} width={contentWidth} onOpen={setSelected} />;
              })}

              {loading && (
                <View style={styles.loading}>
                  <ActivityIndicator color={colors.red} />
                  <Text style={styles.loadingText}>Gerando a consulta e buscando no banco…</Text>
                </View>
              )}
            </View>
          </ScrollView>

          <View style={styles.inputBar}>
            <View style={[styles.inputInner, { width: contentWidth }]}>
              <TextInput
                value={input}
                onChangeText={setInput}
                placeholder="Pergunte sobre qualquer Pokémon"
                placeholderTextColor="#8A94A3"
                style={styles.input}
                maxLength={MAX_LEN}
                onSubmitEditing={() => ask(input)}
                returnKeyType="send"
                editable={!loading}
                accessibilityLabel="Sua pergunta"
              />
              <Pressable
                onPress={() => ask(input)}
                disabled={!canSend}
                style={[styles.send, !canSend && styles.sendDisabled]}
                accessibilityRole="button"
              >
                <Text style={styles.sendText}>Perguntar</Text>
              </Pressable>
            </View>
            {input.length > MAX_LEN - 40 && (
              <Text style={[styles.counter, { width: contentWidth }]}>{input.length}/{MAX_LEN}</Text>
            )}
          </View>
        </KeyboardAvoidingView>

        <PokemonModal pokemon={selected} onClose={() => setSelected(null)} />
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.paper },
  center: { alignItems: 'center', justifyContent: 'center' },
  header: { backgroundColor: colors.red, borderBottomWidth: 4, borderColor: colors.redDark, alignItems: 'center', paddingVertical: 14 },
  headerInner: { flexDirection: 'row', alignItems: 'center', gap: 14 },
  lens: {
    width: 46, height: 46, borderRadius: 23, backgroundColor: '#3FA9F5', borderWidth: 4, borderColor: '#fff',
    alignItems: 'flex-start', justifyContent: 'flex-start', overflow: 'hidden',
  },
  lensGlow: { width: 14, height: 14, borderRadius: 7, backgroundColor: 'rgba(255,255,255,0.75)', margin: 6 },
  title: { fontFamily: fonts.display, fontSize: 26, color: '#fff' },
  subtitle: { fontFamily: fonts.body, fontSize: 13, color: '#FFE3E6' },
  scroll: { alignItems: 'center', paddingVertical: 20 },
  empty: { gap: 10, paddingTop: 12 },
  emptyTitle: { fontFamily: fonts.display, fontSize: 24, color: colors.ink },
  emptyText: { fontFamily: fonts.body, fontSize: 15, lineHeight: 22, color: colors.slate, maxWidth: 560 },
  examples: { gap: 8, marginTop: 6 },
  example: { borderWidth: 1, borderColor: colors.line, backgroundColor: colors.card, borderRadius: 12, paddingVertical: 12, paddingHorizontal: 14 },
  exampleHover: { borderColor: colors.red },
  exampleText: { fontFamily: fonts.bodyMedium, fontSize: 15, color: colors.ink },
  qBubble: { alignSelf: 'flex-end', maxWidth: '85%', backgroundColor: colors.ink, borderRadius: 16, borderBottomRightRadius: 4, paddingVertical: 10, paddingHorizontal: 14 },
  qText: { fontFamily: fonts.bodyMedium, fontSize: 15, color: '#fff' },
  error: { borderLeftWidth: 4, borderColor: colors.red, backgroundColor: '#FBE9EC', padding: 12, borderRadius: 8, gap: 6 },
  errorText: { fontFamily: fonts.body, fontSize: 14, color: colors.ink },
  retry: { fontFamily: fonts.bodyBold, fontSize: 14, color: colors.red, textDecorationLine: 'underline' },
  loading: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  loadingText: { fontFamily: fonts.body, fontSize: 14, color: colors.slate },
  inputBar: { borderTopWidth: 1, borderColor: colors.line, backgroundColor: colors.card, alignItems: 'center', paddingVertical: 10 },
  inputInner: { flexDirection: 'row', gap: 8 },
  input: {
    flex: 1, fontFamily: fonts.body, fontSize: 15, color: colors.ink, backgroundColor: colors.paper,
    borderRadius: 12, paddingHorizontal: 14, paddingVertical: 12,
  },
  send: { backgroundColor: colors.red, borderRadius: 12, paddingHorizontal: 18, justifyContent: 'center' },
  sendDisabled: { opacity: 0.4 },
  sendText: { fontFamily: fonts.bodyBold, color: '#fff', fontSize: 15 },
  counter: { fontFamily: fonts.body, fontSize: 12, color: colors.slate, textAlign: 'right', marginTop: 4 },
});
