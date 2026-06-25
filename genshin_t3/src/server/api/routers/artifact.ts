import { z } from "zod";
import { createTRPCRouter, protectedProcedure } from "~/server/api/trpc";
import { artifactItself } from "~/server/db/schema";
import { eq, desc, count, and } from "drizzle-orm";

// Map the substats array into the individual boolean-ish columns the table uses.
const substatFlags = (substats: string[]) => ({
  percentATK: substats.includes("%ATK") ? 1 : 0,
  percentHP: substats.includes("%HP") ? 1 : 0,
  percentDEF: substats.includes("%DEF") ? 1 : 0,
  atk: substats.includes("ATK") ? 1 : 0,
  hp: substats.includes("HP") ? 1 : 0,
  def: substats.includes("DEF") ? 1 : 0,
  er: substats.includes("ER") ? 1 : 0,
  em: substats.includes("EM") ? 1 : 0,
  critRate: substats.includes("Crit Rate") ? 1 : 0,
  critDMG: substats.includes("Crit DMG") ? 1 : 0,
});

export const artifactRouter = createTRPCRouter({
  getAll: protectedProcedure
    .input(
      z.object({
        limit: z.number().min(1).max(100).default(10),
        page: z.number().min(1).default(1),
      }),
    )
    .query(async ({ ctx, input }) => {
      const offset = (input.page - 1) * input.limit;

      const artifacts = await ctx.db.query.artifactItself.findMany({
        where: eq(artifactItself.userId, ctx.session.user.id),
        orderBy: [desc(artifactItself.createDate), desc(artifactItself.id)],
        limit: input.limit,
        offset: offset,
        with: {
          leveling: true,
        },
      });

      const [total] = await ctx.db
        .select({ count: count() })
        .from(artifactItself)
        .where(eq(artifactItself.userId, ctx.session.user.id));

      return {
        artifacts,
        totalCount: total?.count ?? 0,
        totalPages: Math.ceil((total?.count ?? 0) / input.limit),
      };
    }),

  update: protectedProcedure
    .input(
      z.object({
        id: z.number(),
        set: z.string(),
        type: z.string(),
        mainStat: z.string(),
        numberOfSubstats: z.number().int().min(3).max(4),
        substats: z.array(z.string()),
        score: z.string(),
        source: z.string(),
        unactivatedSubstat: z.string().optional(),
      }),
    )
    .mutation(async ({ ctx, input }) => {
      await ctx.db
        .update(artifactItself)
        .set({
          set: input.set,
          type: input.type,
          mainStat: input.mainStat,
          numberOfSubstat: input.numberOfSubstats,
          whereGotIt: input.source,
          score: input.score,
          percentATK: input.substats.includes("%ATK") ? 1 : 0,
          percentHP: input.substats.includes("%HP") ? 1 : 0,
          percentDEF: input.substats.includes("%DEF") ? 1 : 0,
          atk: input.substats.includes("ATK") ? 1 : 0,
          hp: input.substats.includes("HP") ? 1 : 0,
          def: input.substats.includes("DEF") ? 1 : 0,
          er: input.substats.includes("ER") ? 1 : 0,
          em: input.substats.includes("EM") ? 1 : 0,
          critRate: input.substats.includes("Crit Rate") ? 1 : 0,
          critDMG: input.substats.includes("Crit DMG") ? 1 : 0,
          unactivatedSubstat: input.unactivatedSubstat ?? null,
        })
        .where(
          and(
            eq(artifactItself.id, input.id),
            eq(artifactItself.userId, ctx.session.user.id),
          ),
        );
    }),


  create: protectedProcedure
    .input(
      z.object({
        set: z.string(),
        type: z.string(),
        mainStat: z.string(),
        numberOfSubstats: z.number().int().min(3).max(4),
        substats: z.array(z.string()),
        score: z.string(),
        source: z.string(),
        unactivatedSubstat: z.string().optional(),
      }),
    )
    .mutation(async ({ ctx, input }) => {
      // 1. Create the artifact entry
      const [newArtifact] = await ctx.db
        .insert(artifactItself)
        .values({
          userId: ctx.session.user.id,
          set: input.set,
          type: input.type,
          mainStat: input.mainStat,
          numberOfSubstat: input.numberOfSubstats,
          whereGotIt: input.source,
          score: input.score,
          // Map substats array to individual columns
          percentATK: input.substats.includes("%ATK") ? 1 : 0,
          percentHP: input.substats.includes("%HP") ? 1 : 0,
          percentDEF: input.substats.includes("%DEF") ? 1 : 0,
          atk: input.substats.includes("ATK") ? 1 : 0,
          hp: input.substats.includes("HP") ? 1 : 0,
          def: input.substats.includes("DEF") ? 1 : 0,
          er: input.substats.includes("ER") ? 1 : 0,
          em: input.substats.includes("EM") ? 1 : 0,
          critRate: input.substats.includes("Crit Rate") ? 1 : 0,
          critDMG: input.substats.includes("Crit DMG") ? 1 : 0,
          unactivatedSubstat: input.unactivatedSubstat ?? null,
        })
        .returning({ id: artifactItself.id });

      if (!newArtifact) {
        throw new Error("Failed to create artifact");
      }

      return newArtifact;
    }),

  search: protectedProcedure
    .input(
      z.object({
        set: z.string().nullable().optional(),
        type: z.string().nullable().optional(),
        mainStat: z.string().nullable().optional(),
        numberOfSubstats: z.number().nullable().optional(),
        substats: z.array(z.string()).optional(),
        unactivatedSubstat: z.string().nullable().optional(),
        score: z.string().nullable().optional(),
        source: z.string().nullable().optional(),
        limit: z.number().min(1).max(100).default(10),
        page: z.number().min(1).default(1),
      }),
    )
    .query(async ({ ctx, input }) => {
      const offset = (input.page - 1) * input.limit;
      const filters = [eq(artifactItself.userId, ctx.session.user.id)];

      if (input.set) filters.push(eq(artifactItself.set, input.set));
      if (input.type) filters.push(eq(artifactItself.type, input.type));
      if (input.mainStat) filters.push(eq(artifactItself.mainStat, input.mainStat));
      if (input.numberOfSubstats)
        filters.push(eq(artifactItself.numberOfSubstat, input.numberOfSubstats));
      if (input.unactivatedSubstat)
        filters.push(eq(artifactItself.unactivatedSubstat, input.unactivatedSubstat));
      if (input.score) filters.push(eq(artifactItself.score, input.score));
      if (input.source) filters.push(eq(artifactItself.whereGotIt, input.source));

      if (input.substats && input.substats.length > 0) {
        if (input.substats.includes("%ATK"))
          filters.push(eq(artifactItself.percentATK, 1));
        if (input.substats.includes("%HP"))
          filters.push(eq(artifactItself.percentHP, 1));
        if (input.substats.includes("%DEF"))
          filters.push(eq(artifactItself.percentDEF, 1));
        if (input.substats.includes("ATK"))
          filters.push(eq(artifactItself.atk, 1));
        if (input.substats.includes("HP"))
          filters.push(eq(artifactItself.hp, 1));
        if (input.substats.includes("DEF"))
          filters.push(eq(artifactItself.def, 1));
        if (input.substats.includes("ER"))
          filters.push(eq(artifactItself.er, 1));
        if (input.substats.includes("EM"))
          filters.push(eq(artifactItself.em, 1));
        if (input.substats.includes("Crit Rate"))
          filters.push(eq(artifactItself.critRate, 1));
        if (input.substats.includes("Crit DMG"))
          filters.push(eq(artifactItself.critDMG, 1));
      }

      const artifacts = await ctx.db.query.artifactItself.findMany({
        where: and(...filters),
        orderBy: [desc(artifactItself.createDate)],
        limit: input.limit,
        offset: offset,
        with: {
          leveling: true,
        },
      });

      const [total] = await ctx.db
        .select({ count: count() })
        .from(artifactItself)
        .where(and(...filters));

      return {
        artifacts,
        totalCount: total?.count ?? 0,
        totalPages: Math.ceil((total?.count ?? 0) / input.limit),
      };
    }),

  // Bulk insert from the scanner's exported JSON. Same mapping as `create`,
  // scoped to the signed-in user, done as a single batched insert.
  createMany: protectedProcedure
    .input(
      z.object({
        artifacts: z
          .array(
            z.object({
              set: z.string().min(1),
              type: z.string().min(1),
              mainStat: z.string().min(1),
              numberOfSubstats: z.number().int().min(3).max(4),
              substats: z.array(z.string()),
              score: z.string().min(1),
              source: z.string().min(1),
              unactivatedSubstat: z.string().nullish(),
            }),
          )
          .min(1)
          .max(500),
      }),
    )
    .mutation(async ({ ctx, input }) => {
      const values = input.artifacts.map((a) => ({
        userId: ctx.session.user.id,
        set: a.set,
        type: a.type,
        mainStat: a.mainStat,
        numberOfSubstat: a.numberOfSubstats,
        whereGotIt: a.source,
        score: a.score,
        ...substatFlags(a.substats),
        unactivatedSubstat: a.unactivatedSubstat ?? null,
      }));

      const inserted = await ctx.db
        .insert(artifactItself)
        .values(values)
        .returning({ id: artifactItself.id });

      return { count: inserted.length };
    }),
});
