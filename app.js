* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

:root {
    --bg: #050505;
    --panel: #090909;
    --panel-light: #101010;
    --border: #222222;
    --text: #f2f2f2;
    --muted: #777777;
    --orange: #ff8a24;
    --orange-dark: #b95e16;
}

html,
body {
    width: 100%;
    height: 100%;
    background: var(--bg);
    color: var(--text);
    font-family: Arial, Helvetica, sans-serif;
}

body {
    overflow: hidden;
}

button,
input {
    font-family: inherit;
}

button {
    cursor: pointer;
}

.hidden {
    display: none !important;
}

.page {
    width: 100%;
    height: 100vh;
}

.topbar {
    height: 72px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 38px;
    border-bottom: 1px solid var(--border);
    background: rgba(5, 5, 5, 0.96);
}

.brand {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.brand-main {
    font-size: 21px;
    font-weight: 700;
    letter-spacing: 2px;
}

.brand-sub {
    color: var(--muted);
    font-size: 9px;
    letter-spacing: 3px;
}

.system-status {
    display: flex;
    align-items: center;
    gap: 9px;
    color: #999;
    font-size: 11px;
    letter-spacing: 1px;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--orange);
    box-shadow: 0 0 12px rgba(255, 138, 36, 0.8);
}

.landing-content {
    width: 100%;
    min-height: calc(100vh - 72px);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 50px 25px;
}

.landing-label {
    color: var(--orange);
    font-size: 11px;
    letter-spacing: 5px;
    margin-bottom: 24px;
}

.landing-content h1 {
    font-size: clamp(55px, 10vw, 120px);
    line-height: 0.95;
    letter-spacing: 8px;
    margin-bottom: 30px;
}

.landing-description {
    max-width: 720px;
    color: #888;
    font-size: 16px;
    line-height: 1.8;
    margin-bottom: 38px;
}

.primary-button {
    border: 1px solid var(--orange);
    background: var(--orange);
    color: #050505;
    padding: 15px 34px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
    transition: 0.2s;
}

.primary-button:hover {
    box-shadow: 0 0 28px rgba(255, 138, 36, 0.3);
    transform: translateY(-2px);
}

.feature-grid {
    width: min(900px, 100%);
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-top: 65px;
}

.feature-card {
    padding: 24px;
    background: #090909;
    border: 1px solid var(--border);
    border-radius: 8px;
    text-align: left;
}

.feature-number {
    color: var(--orange);
    font-size: 11px;
    letter-spacing: 2px;
    margin-bottom: 15px;
}

.feature-card h2 {
    font-size: 14px;
    letter-spacing: 1px;
    margin-bottom: 10px;
}

.feature-card p {
    color: #707070;
    font-size: 12px;
    line-height: 1.7;
}

.studio-page {
    width: 100%;
    height: 100vh;
    display: flex;
    flex-direction: column;
    background: #050505;
}

.studio-topbar {
    height: 58px;
    min-height: 58px;
    display: flex;
    align-items: center;
    border-bottom: 1px solid var(--border);
    background: #080808;
}

.studio-brand {
    width: 220px;
    padding-left: 22px;
    font-size: 17px;
    letter-spacing: 2px;
}

.studio-brand span {
    color: var(--orange);
}

.studio-brand strong {
    color: white;
}

.mode-indicator {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 8px;
    color: #888;
    font-size: 10px;
    letter-spacing: 2px;
}

.top-actions {
    display: flex;
    gap: 6px;
    padding-right: 10px;
}

.top-actions button {
    border: 1px solid #292929;
    background: #101010;
    color: #aaa;
    padding: 8px 13px;
    border-radius: 4px;
    font-size: 9px;
    letter-spacing: 1px;
}

.top-actions button:hover {
    border-color: var(--orange);
    color: var(--orange);
}

.studio-layout {
    flex: 1;
    min-height: 0;
    display: grid;
    grid-template-columns: 190px minmax(0, 1fr) 250px;
}

.left-panel,
.right-panel {
    background: #080808;
    border-color: var(--border);
    overflow-y: auto;
}

.left-panel {
    border-right: 1px solid var(--border);
    padding: 15px 10px;
}

.right-panel {
    border-left: 1px solid var(--border);
}

.panel-title {
    color: #666;
    font-size: 9px;
    letter-spacing: 2px;
    margin: 5px 8px 10px;
}

.tool-button,
.create-button {
    width: 100%;
    height: 38px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 0 10px;
    margin-bottom: 4px;
    background: transparent;
    color: #888;
    font-size: 10px;
    letter-spacing: 1px;
}

.tool-button:hover,
.create-button:hover {
    background: #111;
    color: white;
}

.tool-button.active {
    background: rgba(255, 138, 36, 0.1);
    border-color: rgba(255, 138, 36, 0.35);
    color: var(--orange);
}

.tool-button kbd {
    color: #555;
    font-size: 9px;
}

.panel-divider {
    height: 1px;
    background: var(--border);
    margin: 18px 5px;
}

.create-button {
    border-color: #1b1b1b;
    background: #0d0d0d;
    color: #999;
    justify-content: flex-start;
}

.viewport-container {
    position: relative;
    min-width: 0;
    min-height: 0;
    background: #060606;
}

#viewport {
    position: absolute;
    inset: 0;
}

#viewport canvas {
    display: block;
    width: 100%;
    height: 100%;
}

.viewport-label {
    position: absolute;
    top: 13px;
    left: 15px;
    color: #555;
    font-size: 9px;
    letter-spacing: 2px;
    pointer-events: none;
}

.viewport-status {
    position: absolute;
    top: 13px;
    right: 15px;
    display: flex;
    gap: 8px;
    color: #555;
    font-size: 9px;
    letter-spacing: 1px;
    pointer-events: none;
}

.selection-info {
    position: absolute;
    bottom: 105px;
    left: 15px;
    color: #777;
    font-size: 9px;
    letter-spacing: 1px;
    pointer-events: none;
}

.ai-console {
    position: absolute;
    left: 15px;
    right: 15px;
    bottom: 15px;
    padding: 10px;
    border: 1px solid #222;
    border-radius: 7px;
    background: rgba(8, 8, 8, 0.94);
    backdrop-filter: blur(10px);
}

.ai-console-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
    color: #666;
    font-size: 8px;
    letter-spacing: 2px;
}

#aiStatus {
    color: var(--orange);
}

.ai-input-row {
    display: flex;
    gap: 7px;
}

#aiCommand {
    flex: 1;
    height: 34px;
    min-width: 0;
    border: 1px solid #222;
    border-radius: 4px;
    outline: none;
    background: #050505;
    color: white;
    padding: 0 11px;
    font-size: 11px;
}

#aiCommand:focus {
    border-color: var(--orange-dark);
}

#aiSendButton {
    width: 55px;
    border: 1px solid var(--orange);
    border-radius: 4px;
    background: var(--orange);
    color: #050505;
    font-size: 9px;
    font-weight: 700;
}

.panel-section {
    padding: 15px 10px;
    border-bottom: 1px solid var(--border);
}

.object-list {
    display: flex;
    flex-direction: column;
    gap: 3px;
}

.empty-list,
.property-empty {
    padding: 15px 8px;
    color: #444;
    font-size: 10px;
    text-align: center;
}

.object-item {
    height: 34px;
    display: flex;
    align-items: center;
    padding: 0 9px;
    border: 1px solid transparent;
    border-radius: 4px;
    color: #888;
    font-size: 10px;
    cursor: pointer;
}

.object-item:hover {
    background: #111;
    color: white;
}

.object-item.selected {
    background: rgba(255, 138, 36, 0.1);
    border-color: rgba(255, 138, 36, 0.3);
    color: var(--orange);
}

.object-icon {
    width: 22px;
    color: #555;
}

.property-row {
    display: grid;
    grid-template-columns: 70px 1fr;
    gap: 7px;
    align-items: center;
    margin-bottom: 7px;
}

.property-label {
    color: #555;
    font-size: 9px;
}

.property-value {
    min-width: 0;
    padding: 7px;
    border: 1px solid #1d1d1d;
    border-radius: 3px;
    background: #0d0d0d;
    color: #aaa;
    font-size: 9px;
}

@media (max-width: 900px) {
    .studio-layout {
        grid-template-columns: 150px minmax(0, 1fr);
    }

    .right-panel {
        display: none;
    }

    .feature-grid {
        grid-template-columns: 1fr;
        max-width: 400px;
    }
}

@media (max-width: 600px) {
    .studio-layout {
        grid-template-columns: 1fr;
    }

    .left-panel {
        display: none;
    }

    .studio-brand {
        width: auto;
        padding-left: 12px;
    }

    .mode-indicator {
        display: none;
    }

    .top-actions button {
        padding: 7px;
    }

    .landing-content h1 {
        font-size: 48px;
        letter-spacing: 4px;
    }
}
