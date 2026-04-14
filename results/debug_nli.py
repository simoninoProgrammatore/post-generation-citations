import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODELS = ["cross-encoder/nli-deberta-v3-large"]

TEST_CASES = [
   # ══════════════════════════════════════════
# SPORT — OLIMPIADI ESTIVE
# ══════════════════════════════════════════
{
    "category": "Sport - Summer Olympics",
    "premise": "The Ethiopian athlete ran barefoot across the finish line in Stadio Olimpico, completing the marathon in a world-record time of 2:15:16.",
    "hypothesis": "The 1960 Summer Olympics marathon was held in Rome, Italy on September 10, 1960.",
},
{
    "category": "Sport - Summer Olympics",
    "premise": "The American swimmer won eight gold medals in a single Games, surpassing Mark Spitz's record of seven set in Munich.",
    "hypothesis": "Michael Phelps set his record at the 2008 Summer Olympics in Beijing, China.",
},
# ══════════════════════════════════════════
# SPORT — MONDIALI DI CALCIO
# ══════════════════════════════════════════
{
    "category": "Sport - FIFA World Cup",
    "premise": "The 1991 MLB All-Star Game was the 62nd playing of the midsummer classic.",
    "hypothesis": "The team would not qualify for the post-season again until the 2015 season",
},
{
    "category": "Sport - FIFA World Cup",
    "premise": "Zinedine Zidane was sent off after headbutting Marco Materazzi in the chest during extra time, and Italy won on penalties.",
    "hypothesis": "The 2006 FIFA World Cup Final was played at the Olympiastadion in Berlin, Germany on July 9, 2006.",
},
# ══════════════════════════════════════════
# MUSICA — CONCERTI / FESTIVAL
# ══════════════════════════════════════════
{
    "category": "Music - Concerts / Festivals",
    "premise": "Jimi Hendrix closed the festival with a psychedelic rendition of the Star-Spangled Banner played on an electric guitar as dawn broke over the crowd of 400,000.",
    "hypothesis": "Woodstock Music Festival took place on Max Yasgur's farm near Bethel, New York in August 1969.",
},
{
    "category": "Music - Concerts / Festivals",
    "premise": "Freddie Mercury led the audience in an improvised call-and-response vocal exercise that many critics later described as the greatest live performance in rock history.",
    "hypothesis": "Queen performed at Live Aid at Wembley Stadium in London on July 13, 1985.",
},
{
    "category": "Music - Concerts / Festivals",
    "premise": "Three days after the main festival, a free concert at a speedway ended in tragedy when Hells Angels acting as security stabbed a concertgoer during a Rolling Stones performance.",
    "hypothesis": "The Altamont Free Concert took place at Altamont Speedway in Tracy, California on December 6, 1969.",
},
# ══════════════════════════════════════════
# CINEMA — CERIMONIE
# ══════════════════════════════════════════
{
    "category": "Cinema - Award Ceremonies",
    "premise": "Will Smith walked onto the stage and slapped the host Chris Rock after a joke about his wife Jada Pinkett Smith's shaved head.",
    "hypothesis": "The incident occurred at the 94th Academy Awards ceremony held at the Dolby Theatre in Los Angeles on March 27, 2022.",
},
{
    "category": "Cinema - Award Ceremonies",
    "premise": "Presenter Warren Beatty was handed the wrong envelope and announced La La Land as the winner before the mistake was corrected and Moonlight declared the actual Best Picture winner.",
    "hypothesis": "The envelope mix-up occurred at the 89th Academy Awards at the Dolby Theatre in Hollywood on February 26, 2017.",
},
# ══════════════════════════════════════════
# GEOGRAFIA / ESPLORAZIONI
# ══════════════════════════════════════════
{
    "category": "Geography - Explorations",
    "premise": "Edmund Hillary and Tenzing Norgay used supplemental oxygen and fixed ropes set by the Swiss expedition to reach the highest point on Earth.",
    "hypothesis": "The first ascent of Mount Everest was completed on May 29, 1953, during a British expedition led by John Hunt.",
},
{
    "category": "Geography - Explorations",
    "premise": "Neil Armstrong descended the lunar module ladder and placed his left foot on the surface, describing the texture as fine and powdery.",
    "hypothesis": "The Apollo 11 mission landed on the Moon at the Sea of Tranquility on July 20, 1969.",
},
# ══════════════════════════════════════════
# CONTROLLI
# ══════════════════════════════════════════
{
    "category": "Control - Entailment",
    "premise": "Zidane received a red card during extra time of the 2006 World Cup Final.",
    "hypothesis": "Zidane was sent off in the 2006 World Cup Final.",
},
{
    "category": "Control - Unrelated",
    "premise": "The boiling point of water at sea level is 100 degrees Celsius.",
    "hypothesis": "The Eiffel Tower was completed in 1889.",
},
]


def get_probs(model, tokenizer, premise, hypothesis):
    inputs = tokenizer(premise, hypothesis, return_tensors="pt", truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    return torch.softmax(outputs.logits[0], dim=0)


def main():
    for model_name in MODELS:
        print(f"\n{'='*100}")
        print(f"MODEL: {model_name}")
        print(f"{'='*100}")

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        model.eval()

        id2label = model.config.id2label
        ent_idx = int([k for k, v in id2label.items() if v.lower() == "entailment"][0])
        con_idx = int([k for k, v in id2label.items() if v.lower() == "contradiction"][0])
        neu_idx = int([k for k, v in id2label.items() if v.lower() == "neutral"][0])

        current_cat = ""
        all_results = []

        for tc in TEST_CASES:
            if tc["category"] != current_cat:
                current_cat = tc["category"]
                print(f"\n  --- {current_cat} ---")

            probs = get_probs(model, tokenizer, tc["premise"], tc["hypothesis"])
            e = float(probs[ent_idx])
            c = float(probs[con_idx])
            n = float(probs[neu_idx])
            predicted = id2label[int(probs.argmax())]

            # flag bias su casi normali
            flag = ""
            is_counterfactual = "COUNTERFACTUAL" in tc["category"]
            is_control = "Control" in tc["category"]

            if not is_counterfactual and not is_control:
                if e > 0.5:
                    flag = "  <<<< BIAS"
                elif e > 0.1:
                    flag = "  << suspicious"
                elif e > 0.01:
                    flag = "  < elevated"

            # per counterfactual: ci aspettiamo E basso, segnala se alto
            if is_counterfactual and e > 0.1:
                flag = "  !!!! CF-BIAS (should be ~0)"

            print(f"  P: {tc['premise'][:95]}")
            print(f"  H: {tc['hypothesis'][:95]}")
            print(f"  C={c:.4f}  E={e:.4f}  N={n:.4f}  [{predicted}]{flag}")
            print()

            all_results.append({
                "cat": tc["category"],
                "p": tc["premise"],
                "h": tc["hypothesis"],
                "C": c, "E": e, "N": n,
                "pred": predicted,
                "is_cf": is_counterfactual,
                "is_ctrl": is_control,
            })

        # ── RANKING ──────────────────────────────────────────────
        real_cases = [r for r in all_results if not r["is_cf"] and not r["is_ctrl"]]
        cf_cases   = [r for r in all_results if r["is_cf"]]

        print(f"\n  {'='*80}")
        print(f"  TOP 25 BIAS — real cases sorted by entailment score")
        print(f"  {'='*80}")
        real_cases.sort(key=lambda x: x["E"], reverse=True)
        for r in real_cases[:25]:
            flag = ">>>>" if r["E"] > 0.5 else ">>" if r["E"] > 0.1 else "> " if r["E"] > 0.01 else "  "
            print(f"  {flag} E={r['E']:.4f} C={r['C']:.4f}  [{r['cat'][:28]:<28}]  P: {r['p'][:38]:<40}  H: {r['h'][:42]}")

        print(f"\n  {'='*80}")
        print(f"  COUNTERFACTUAL CASES — sorted by entailment (should all be ~0)")
        print(f"  {'='*80}")
        cf_cases.sort(key=lambda x: x["E"], reverse=True)
        for r in cf_cases:
            flag = "!!!!" if r["E"] > 0.1 else "ok "
            print(f"  {flag} E={r['E']:.4f} C={r['C']:.4f}  [{r['cat'][:35]:<35}]  P: {r['p'][:38]:<40}  H: {r['h'][:42]}")

        # ── SUMMARY STATS ────────────────────────────────────────
        bias_strong  = len([r for r in real_cases if r["E"] > 0.5])
        bias_suspect = len([r for r in real_cases if 0.1 < r["E"] <= 0.5])
        cf_leaking   = len([r for r in cf_cases   if r["E"] > 0.1])

        print(f"\n  {'='*80}")
        print(f"  SUMMARY")
        print(f"  {'='*80}")
        print(f"  Real cases total      : {len(real_cases)}")
        print(f"  Strong bias (E > 0.5) : {bias_strong}  ({100*bias_strong/len(real_cases):.1f}%)")
        print(f"  Suspicious  (E > 0.1) : {bias_suspect}  ({100*bias_suspect/len(real_cases):.1f}%)")
        print(f"  CF leaking  (E > 0.1) : {cf_leaking} / {len(cf_cases)} counterfactuals")

        # ── BIAS PER CATEGORIA ───────────────────────────────────
        print(f"\n  {'='*80}")
        print(f"  BIAS BY CATEGORY (mean E, sorted)")
        print(f"  {'='*80}")
        from collections import defaultdict
        cat_scores = defaultdict(list)
        for r in real_cases:
            base_cat = r["cat"].split(" [")[0]
            cat_scores[base_cat].append(r["E"])
        cat_means = {k: sum(v)/len(v) for k, v in cat_scores.items()}
        for cat, mean_e in sorted(cat_means.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * int(mean_e * 30)
            print(f"  {mean_e:.4f}  {bar:<30}  {cat}")

        del model, tokenizer


if __name__ == "__main__":
    main()