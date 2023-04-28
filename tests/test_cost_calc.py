alpha = 5.65e-4
beta = 0.5941
theta = 0.6604
delta = 80.599
epsilon = 3.8085e-55
phi = -0.3553
gamma = 1.5691

quantity = 1
year = 2025
block = 1
difficulty = 0
mass = 1000
spec = 1.92


cost = alpha * quantity ** beta * mass ** theta * \
        delta ** spec * epsilon ** (1/(year-1900)) * \
        block ** phi * gamma ** difficulty

print(cost)

# approximate 80% increase from 1999 to 2023 from inflation
cost_adjusted = 1.8 * cost