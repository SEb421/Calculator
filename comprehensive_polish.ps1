# PowerShell script for comprehensive polish enhancements
$file = "C:\Users\shuli\Downloads\Calculator\index.html"
$content = Get-Content $file -Raw

# 1. Add smooth scroll to html
$content = $content -replace '<style>', @"
<style>
        /* Smooth Scroll */
        html {
            scroll-behavior: smooth;
        }
"@

# 2. Add comprehensive transition and hover enhancements to style section
$oldStyleEnd = '        /\* Premium Desktop Shadows \*/'
$newTransitions = @"
        /* Smooth Transitions & Hover States */
        * {
            transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
        }
        
        /* Button Hover Enhancement */
        button:not(:disabled):hover {
            transform: translateY(-1px);
        }
        
        button:not(:disabled):active {
            transform: translateY(0);
        }
        
        /* Input Focus Rings */
        input:focus, textarea:focus {
            outline: 2px solid rgb(59, 130, 246);
            outline-offset: 2px;
        }
        
        .dark input:focus, .dark textarea:focus {
            outline-color: rgb(96, 165, 250);
        }
        
        /* Glass Card Hover (Desktop only) */
        @media (min-width: 768px) {
            .glass-card:hover {
                box-shadow: 
                    0 2px 4px rgba(0,0,0,0.06),
                    0 8px 16px rgba(0,0,0,0.1),
                    0 32px 64px rgba(0,0,0,0.04);
            }
        }
        
        /* Tab Button Enhancement */
        .tab-button {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        /* Breakdown Visual Grouping */
        .breakdown-product {
            background: linear-gradient(to right, rgb(239, 246, 255, 0.3), rgb(224, 242, 254, 0.3));
        }
        
        .dark .breakdown-product {
            background: linear-gradient(to right, rgb(30, 58, 138, 0.1), rgb(30, 64, 175, 0.1));
        }
        
        .breakdown-logistics {
            background: linear-gradient(to right, rgb(254, 252, 232, 0.3), rgb(254, 243, 199, 0.3));
        }
        
        .dark .breakdown-logistics {
            background: linear-gradient(to right, rgb(120, 53, 15, 0.1), rgb(133, 77, 14, 0.1));
        }
        
        .breakdown-fees {
            background: linear-gradient(to right, rgb(250, 245, 255, 0.3), rgb(243, 232, 255, 0.3));
        }
        
        .dark .breakdown-fees {
            background: linear-gradient(to right, rgb(76, 29, 149, 0.1), rgb(88, 28, 135, 0.1));
        }

        /* Premium Desktop Shadows */
"@

$content = $content -replace '        /\* Premium Desktop Shadows \*/', $newTransitions

Set-Content $file $content -NoNewline
Write-Host "Applied comprehensive polish enhancements"
