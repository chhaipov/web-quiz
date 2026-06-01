import { useState, useEffect, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import { gameApi } from '../api';

const IMG = '/images/invoker';

const ORBS = {
  Q: { key: 'Q', name: 'Quas', img: `${IMG}/quas.png`, color: '#5b9ee9' },
  W: { key: 'W', name: 'Wex', img: `${IMG}/wex.png`, color: '#c77dea' },
  E: { key: 'E', name: 'Exort', img: `${IMG}/exort.png`, color: '#ef8a47' },
};

const SPELLS = [
  { name: 'Cold Snap', combo: 'QQQ', img: `${IMG}/cold_snap.png` },
  { name: 'Ghost Walk', combo: 'QQW', img: `${IMG}/ghost_walk.png` },
  { name: 'Ice Wall', combo: 'QQE', img: `${IMG}/ice_wall.png` },
  { name: 'EMP', combo: 'WWW', img: `${IMG}/emp.png` },
  { name: 'Tornado', combo: 'QWW', img: `${IMG}/tornado.png` },
  { name: 'Alacrity', combo: 'WWE', img: `${IMG}/alacrity.png` },
  { name: 'Sun Strike', combo: 'EEE', img: `${IMG}/sun_strike.png` },
  { name: 'Forge Spirit', combo: 'QEE', img: `${IMG}/forge_spirit.png` },
  { name: 'Chaos Meteor', combo: 'WEE', img: `${IMG}/chaos_meteor.png` },
  { name: 'Deafening Blast', combo: 'QWE', img: `${IMG}/deafening_blast.png` },
];

const START_TIME = 8.0;
const MIN_TIME = 1.5;
const SHRINK_PER_SPELL = 0.25;
const TICK_MS = 50;

function sortCombo(c) {
  const order = { Q: 0, W: 1, E: 2 };
  return c.split('').sort((a, b) => order[a] - order[b]).join('');
}

function pickRandom(exclude) {
  const pool = SPELLS.filter((s) => s.name !== exclude);
  return pool[Math.floor(Math.random() * pool.length)];
}

function getAllowedTime(spellCount) {
  return Math.max(MIN_TIME, START_TIME - spellCount * SHRINK_PER_SPELL);
}

function SpellSidebar() {
  return (
    <div className="invoker-sidebar">
      <h3>Spells</h3>
      <div className="invoker-sidebar-list">
        {SPELLS.map((s) => (
          <div key={s.name} className="invoker-sidebar-item">
            <img src={s.img} alt={s.name} />
            <span className="invoker-sidebar-name">{s.name}</span>
            <span className="invoker-sidebar-combo">
              {s.combo.split('').map((o, i) => (
                <span key={i} className={`invoker-orb-letter invoker-orb-${o}`}>{o}</span>
              ))}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function InvokerGame() {
  const [screen, setScreen] = useState('menu');
  const [orbs, setOrbs] = useState([]);
  const [target, setTarget] = useState(null);
  const [score, setScore] = useState(0);
  const [combo, setCombo] = useState(0);
  const [bestCombo, setBestCombo] = useState(0);
  const [spellCount, setSpellCount] = useState(0);
  const [timeLeft, setTimeLeft] = useState(START_TIME);
  const [allowedTime, setAllowedTime] = useState(START_TIME);
  const [feedback, setFeedback] = useState(null);
  const [history, setHistory] = useState([]);
  const [attempts, setAttempts] = useState([]);
  const [reward, setReward] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [highScore, setHighScore] = useState(() => {
    return parseInt(localStorage.getItem('invoker_highscore') || '0', 10);
  });
  const timerRef = useRef(null);
  const feedbackTimer = useRef(null);
  const screenRef = useRef(screen);
  screenRef.current = screen;

  const startGame = useCallback(() => {
    setScreen('playing');
    setOrbs([]);
    setScore(0);
    setCombo(0);
    setBestCombo(0);
    setSpellCount(0);
    setAllowedTime(START_TIME);
    setTimeLeft(START_TIME);
    setFeedback(null);
    setHistory([]);
    setAttempts([]);
    setReward(null);
    setTarget(pickRandom(null));
  }, []);

  useEffect(() => {
    if (screen !== 'playing') return;
    timerRef.current = setInterval(() => {
      setTimeLeft((t) => {
        const next = t - TICK_MS / 1000;
        if (next <= 0) {
          clearInterval(timerRef.current);
          setTimeout(() => {
            if (screenRef.current === 'playing') setScreen('results');
          }, 0);
          return 0;
        }
        return next;
      });
    }, TICK_MS);
    return () => clearInterval(timerRef.current);
  }, [screen]);

  useEffect(() => {
    if (screen === 'results') {
      setHighScore((prev) => {
        const best = Math.max(prev, score);
        localStorage.setItem('invoker_highscore', String(best));
        return best;
      });
      if (attempts.length > 0 && localStorage.getItem('access')) {
        setSubmitting(true);
        gameApi
          .submitScore(attempts)
          .then((data) => setReward(data))
          .catch(() => setReward(null))
          .finally(() => setSubmitting(false));
      }
    }
  }, [screen]);

  const pushOrb = useCallback(
    (key) => {
      if (screen !== 'playing') return;
      setOrbs((prev) => {
        const next = [...prev, key];
        if (next.length > 3) next.shift();
        return next;
      });
    },
    [screen],
  );

  const invoke = useCallback(() => {
    if (screen !== 'playing' || orbs.length < 3) return;
    const current = sortCombo(orbs.join(''));
    const needed = sortCombo(target.combo);

    const orbStr = orbs.join('');
    if (current === needed) {
      const pts = 1 + Math.floor(combo / 3);
      setScore((s) => s + pts);
      setCombo((c) => {
        const next = c + 1;
        setBestCombo((b) => Math.max(b, next));
        return next;
      });
      setSpellCount((n) => {
        const next = n + 1;
        const newAllowed = getAllowedTime(next);
        setAllowedTime(newAllowed);
        setTimeLeft(newAllowed);
        return next;
      });
      setFeedback({ type: 'correct', text: `+${pts}` });
      setHistory((h) => [{ spell: target.name, img: target.img, correct: true }, ...h].slice(0, 20));
      setAttempts((a) => [...a, { spell: target.name, answer: orbStr, correct: true }]);
      setTarget(pickRandom(target.name));
    } else {
      setCombo(0);
      setFeedback({ type: 'wrong', text: 'Miss!' });
      setHistory((h) => [{ spell: target.name, img: target.img, correct: false }, ...h].slice(0, 20));
      setAttempts((a) => [...a, { spell: target.name, answer: orbStr, correct: false }]);
    }

    clearTimeout(feedbackTimer.current);
    feedbackTimer.current = setTimeout(() => setFeedback(null), 800);
    setOrbs([]);
  }, [screen, orbs, target, combo]);

  useEffect(() => {
    if (screen !== 'playing') return;
    const handler = (e) => {
      const k = e.key.toUpperCase();
      if (k === 'Q' || k === 'W' || k === 'E') pushOrb(k);
      else if (k === 'R' || k === 'D') invoke();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [screen, pushOrb, invoke]);

  // ---- MENU ----
  if (screen === 'menu') {
    return (
      <div className="page invoker-page">
        <div className="invoker-menu">
          <img src={`${IMG}/invoke.png`} alt="Invoke" className="invoker-menu-icon" />
          <h1>Invoker Challenge</h1>
          <p className="invoker-menu-desc">
            Invoke the displayed spell before time runs out!<br />
            The timer gets <strong>faster</strong> with each correct invoke.<br />
            Timeout = game over.<br /><br />
            Press <kbd>Q</kbd> <kbd>W</kbd> <kbd>E</kbd> for orbs, then <kbd>R</kbd> to invoke.
          </p>
          <div className="invoker-spell-ref">
            <h3>Spell Reference</h3>
            <div className="invoker-ref-grid">
              {SPELLS.map((s) => (
                <div key={s.name} className="invoker-ref-item">
                  <img src={s.img} alt={s.name} />
                  <div>
                    <span className="invoker-ref-name">{s.name}</span>
                    <span className="invoker-ref-combo">
                      {s.combo.split('').map((o, i) => (
                        <span key={i} className={`invoker-orb-letter invoker-orb-${o}`}>{o}</span>
                      ))}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
          {highScore > 0 && <p className="invoker-menu-hs">High Score: {highScore}</p>}
          <button className="btn btn-primary btn-lg invoker-start-btn" onClick={startGame}>
            Start Game
          </button>
          <Link to="/" className="invoker-back-link">Back to Shop</Link>
        </div>
      </div>
    );
  }

  // ---- RESULTS ----
  if (screen === 'results') {
    const isNewHigh = score >= highScore && score > 0;
    const correct = history.filter((h) => h.correct).length;
    const wrong = history.filter((h) => !h.correct).length;
    const accuracy = correct + wrong > 0 ? Math.round((correct / (correct + wrong)) * 100) : 0;

    return (
      <div className="page invoker-page">
        <div className="invoker-results">
          <h1>{isNewHigh ? 'New High Score!' : 'Time\'s Up!'}</h1>
          <div className="invoker-results-score">{score}</div>
          <p className="invoker-results-speed">
            Reached {allowedTime.toFixed(1)}s per spell ({spellCount} spells invoked)
          </p>
          <div className="invoker-results-stats">
            <div className="invoker-stat-box">
              <span className="invoker-stat-val text-success">{correct}</span>
              <span className="invoker-stat-lbl">Correct</span>
            </div>
            <div className="invoker-stat-box">
              <span className="invoker-stat-val text-danger">{wrong}</span>
              <span className="invoker-stat-lbl">Wrong</span>
            </div>
            <div className="invoker-stat-box">
              <span className="invoker-stat-val">{accuracy}%</span>
              <span className="invoker-stat-lbl">Accuracy</span>
            </div>
            <div className="invoker-stat-box">
              <span className="invoker-stat-val" style={{ color: '#c77dea' }}>{bestCombo}</span>
              <span className="invoker-stat-lbl">Best Combo</span>
            </div>
          </div>
          {submitting && (
            <div className="invoker-reward-info">
              <span className="invoker-reward-loading">Submitting results...</span>
            </div>
          )}
          {reward && !submitting && (
            <div className="invoker-reward-info">
              <span className="invoker-reward-icon">💰</span>
              <span className="invoker-reward-text">
                +${reward.reward} added to wallet (Server verified: {reward.verified_score} correct)
              </span>
              <span className="invoker-reward-balance">Balance: ${reward.new_balance}</span>
            </div>
          )}
          {!reward && !submitting && !localStorage.getItem('access') && (
            <div className="invoker-reward-info invoker-reward-guest">
              <Link to="/login">Log in</Link> to earn wallet rewards!
            </div>
          )}
          <div className="invoker-results-actions">
            <button className="btn btn-primary btn-lg" onClick={startGame}>Play Again</button>
            <Link to="/" className="btn btn-outline">Back to Shop</Link>
          </div>
        </div>
      </div>
    );
  }

  // ---- PLAYING ----
  const timerPct = allowedTime > 0 ? (timeLeft / allowedTime) * 100 : 0;
  const timerColor = timerPct <= 25 ? '#f44' : timerPct <= 50 ? '#f90' : 'var(--gold)';
  const speed = allowedTime.toFixed(1);

  return (
    <div className="page invoker-page invoker-page-playing">
      <div className="invoker-game-layout">
        {/* Main game area */}
        <div className="invoker-game-main">
          {/* HUD */}
          <div className="invoker-hud">
            <div className="invoker-hud-score">
              <span className="invoker-hud-label">Score</span>
              <span className="invoker-hud-value">{score}</span>
            </div>
            <div className="invoker-hud-timer">
              <div className="invoker-timer-bar">
                <div
                  className="invoker-timer-fill"
                  style={{ width: `${timerPct}%`, background: timerColor }}
                />
              </div>
              <span className="invoker-timer-text" style={{ color: timerColor }}>{timeLeft.toFixed(1)}s</span>
            </div>
            <div className="invoker-hud-combo">
              <span className="invoker-hud-label">Combo</span>
              <span className="invoker-hud-value" style={{ color: combo > 0 ? '#c77dea' : 'var(--text-muted)' }}>
                x{combo}
              </span>
            </div>
          </div>

          {/* Speed indicator */}
          <div className="invoker-speed-badge" style={{ color: timerPct <= 50 ? '#f90' : 'var(--text-muted)' }}>
            {speed}s per spell
          </div>

          {/* Target spell — no combo hint */}
          <div className="invoker-target">
            <span className="invoker-target-label">INVOKE</span>
            <div className={`invoker-target-spell ${timerPct <= 25 ? 'invoker-target-urgent' : ''}`}>
              <img src={target.img} alt={target.name} className="invoker-target-img" />
              <h2 className="invoker-target-name">{target.name}</h2>
            </div>
          </div>

          {/* Feedback */}
          {feedback && (
            <div className={`invoker-feedback invoker-feedback-${feedback.type}`}>
              {feedback.text}
            </div>
          )}

          {/* Current orbs */}
          <div className="invoker-current-orbs">
            {[0, 1, 2].map((i) => (
              <div key={i} className={`invoker-orb-slot ${orbs[i] ? `invoker-orb-active-${orbs[i]}` : ''}`}>
                {orbs[i] ? (
                  <img src={ORBS[orbs[i]].img} alt={orbs[i]} />
                ) : (
                  <span className="invoker-orb-empty" />
                )}
              </div>
            ))}
          </div>

          {/* Orb buttons */}
          <div className="invoker-controls">
            {['Q', 'W', 'E'].map((k) => (
              <button
                key={k}
                className={`invoker-orb-btn invoker-orb-btn-${k}`}
                onClick={() => pushOrb(k)}
              >
                <img src={ORBS[k].img} alt={ORBS[k].name} />
                <kbd>{k}</kbd>
              </button>
            ))}
            <button
              className="invoker-invoke-btn"
              onClick={invoke}
              disabled={orbs.length < 3}
            >
              <img src={`${IMG}/invoke.png`} alt="Invoke" />
              <kbd>R</kbd>
            </button>
          </div>

          {/* History */}
          {history.length > 0 && (
            <div className="invoker-history">
              {history.map((h, i) => (
                <div key={i} className={`invoker-history-item ${h.correct ? 'invoker-hist-ok' : 'invoker-hist-fail'}`}>
                  <img src={h.img} alt={h.spell} />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Sidebar spell reference */}
        <SpellSidebar />
      </div>
    </div>
  );
}
